import json
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import connection
from django.utils import timezone

from apps.organizations.models import OrganizationMembership

from .balances import landlord_totals
from .models import BalanceSnapshot, Payout, ProviderAccount, Withdrawal
from .provider import ProviderResult
from .services import approve_destination
from .testing import ACCOUNT, client_for, paid
from .withdrawals import (
    balance,
    cancel_withdrawal,
    fee_for,
    largest_withdrawal,
    process_withdrawal,
    request_withdrawal,
)

pytestmark = pytest.mark.django_db
D = Decimal


@pytest.fixture(autouse=True)
def manual(settings):
    settings.LENCO_AUTOMATIC_PAYOUTS = False


def withdraw(home, amount="50.00", fee="12.00", key=None):
    return request_withdrawal(
        organization=home["org"],
        user=home["manager"],
        amount=amount,
        fee=fee,
        idempotency_key=key or uuid.uuid4(),
    )


def transfer(row, state="successful", **overrides):
    data = {
        "id": "provider-transfer-1",
        "reference": row.reference,
        "amount": str(row.amount),
        "currency": "ZMW",
        "accountId": ACCOUNT,
        "status": state,
        "fee": "8.50",
        "creditAccount": {"type": "mobile-money", "phone": "0971111111", "operator": "airtel"},
    }
    data.update(overrides)
    return ProviderResult({"status": True, "data": data}, 200)


def send(row, *responses):
    with patch("apps.payments.withdrawals.Provider") as provider:
        provider.return_value.request.side_effect = list(responses)
        process_withdrawal(row)
    row.refresh_from_db()
    return provider.return_value.request.call_args_list


def test_fee_bands_and_largest_amount():
    assert fee_for("mobile-money", D("1000.00")) == D("12.00")
    assert fee_for("mobile-money", D("1000.01")) == D("25.00")
    assert fee_for("bank-account", D("50.00")) == D("10.00")
    assert fee_for("mobile-money", D("50000.01")) is None
    assert largest_withdrawal("mobile-money", D("1012.00")) == D("1000.00")
    assert largest_withdrawal("mobile-money", D("1030.00")) == D("1005.00")
    assert largest_withdrawal("mobile-money", D("1020.00")) == D("1000.00")
    assert largest_withdrawal("mobile-money", D("21.99")) is None


def test_settled_rent_joins_the_balance_without_a_payout(home):
    from .services import reconcile_collection
    from .testing import collection_result

    row = paid(home, settled=False)
    assert balance(home["org"])["awaiting_settlement"] == row.amount
    assert balance(home["org"])["available"] == 0
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        reconcile_collection(row)
    assert not Payout.objects.exists()
    totals = balance(home["org"])
    assert (totals["available"], totals["awaiting_settlement"]) == (D("97.50"), 0)


def test_legacy_payouts_hold_their_rent_until_they_fail(home):
    row = paid(home)
    payout = Payout.objects.create(collection=row, amount=row.settled_amount)
    assert balance(home["org"])["available"] == 0
    Payout.objects.filter(pk=payout.pk).update(status="failed")
    assert balance(home["org"])["available"] == D("97.50")


def test_request_reserves_amount_and_fee_once(home):
    paid(home)
    key = uuid.uuid4()
    row = withdraw(home, key=key)
    assert withdraw(home, key=key) == row
    assert (row.amount, row.fee_reserved, row.status) == (D("50.00"), D("12.00"), "queued")
    assert balance(home["org"])["available"] == D("35.50")
    assert balance(home["org"])["processing"] == D("62.00")
    with pytest.raises(Exception, match="more than your balance"):
        withdraw(home, amount="30.00")
    with pytest.raises(Exception, match="different amount"):
        withdraw(home, amount="20.00", key=key)


@pytest.mark.parametrize(
    "amount,fee,message",
    [
        ("50.00", "10.00", "fee has changed"),
        ("5.00", "12.00", "smallest withdrawal"),
        ("90.00", "12.00", "more than your balance"),
    ],
)
def test_request_rejects_a_changed_fee_and_bad_amounts(home, amount, fee, message):
    paid(home)
    with pytest.raises(Exception, match=message):
        withdraw(home, amount=amount, fee=fee)
    assert not Withdrawal.objects.exists()


def test_request_needs_payouts_and_a_receiving_account(home, settings):
    paid(home)
    settings.LENCO_PAYOUTS_ENABLED = False
    with pytest.raises(Exception, match="not enabled"):
        withdraw(home)
    settings.LENCO_PAYOUTS_ENABLED = True
    home["destination"].enabled = False
    home["destination"].save()
    with pytest.raises(Exception, match="receiving account"):
        withdraw(home)


def test_withdrawal_is_sent_once_and_charges_the_reported_fee(home):
    paid(home)
    row = withdraw(home)
    calls = send(row, transfer(row))
    assert [call.args[0] for call in calls] == ["withdrawal_submit"]
    payload = calls[0].kwargs["payload"]
    assert payload["phone"] == "+260971111111" and payload["operator"] == "airtel"
    assert payload["amount"] == 50.0 and payload["reference"] == row.reference
    assert row.status == "successful" and row.fee_charged == D("8.50")
    assert row.next_check_at is None and row.confirmed_at
    totals = balance(home["org"])
    assert totals["available"] == D("39.00")
    assert totals["withdrawn_this_month"] == D("50.00")
    assert totals["fees_this_month"] == D("8.50")
    assert send(row) == []  # finished: nothing more is asked


def test_bank_withdrawal_sends_the_bank_details(home):
    approve_destination(
        organization=home["org"],
        user=home["manager"],
        kind="bank-account",
        bank_id="bank-zanaco",
        bank_name="Zanaco",
        account_number="0921445509210",
        account_name="MUTALE BANDA",
        reason="Test bank account",
    )
    paid(home)
    row = withdraw(home, fee="10.00")
    result = transfer(
        row,
        creditAccount={
            "type": "bank-account",
            "accountNumber": "0921445509210",
            "bank": {"id": "bank-zanaco", "name": "Zanaco"},
        },
    )
    calls = send(row, result)
    payload = calls[0].kwargs["payload"]
    assert payload["accountNumber"] == "0921445509210" and payload["bankId"] == "bank-zanaco"
    assert "phone" not in payload
    assert row.status == "successful" and row.fee_charged == D("8.50")


def test_timeout_is_checked_by_reference_never_resent(home):
    paid(home)
    row = withdraw(home)
    send(row, ProviderResult({}, None, "network_error"))
    assert row.status == "submitting"
    Withdrawal.objects.filter(pk=row.pk).update(next_check_at=timezone.now())
    calls = send(row, transfer(row, "pending"))
    assert [call.args[0] for call in calls] == ["withdrawal_status"]
    assert row.status == "pending"


def test_refused_submission_returns_the_money(home):
    paid(home)
    row = withdraw(home)
    refused = ProviderResult(
        {"status": False, "message": "The API key does not have permission"}, 403, "http_error"
    )
    send(row, refused)
    assert row.status == "failed" and row.issue == "withdrawal_refused"
    assert balance(home["org"])["available"] == D("97.50")


def test_failed_transfer_without_currency_still_returns_the_money(home):
    paid(home)
    row = withdraw(home)
    send(row, transfer(row, "failed", currency=None, creditAccount=None, fee=None))
    assert row.status == "failed" and row.issue == "withdrawal_failed"
    assert balance(home["org"])["available"] == D("97.50")


def test_mismatch_holds_the_money_for_review(home):
    paid(home)
    row = withdraw(home)
    send(row, transfer(row, amount="49.00"))
    assert row.status == "review" and row.issue == "withdrawal_details_mismatch"
    assert balance(home["org"])["available"] == D("35.50")


def test_landlord_never_pays_more_than_the_confirmed_fee(home):
    paid(home)
    row = withdraw(home)
    send(row, transfer(row, fee="20.00"))
    assert row.fee_charged == D("12.00") and row.issue == "withdrawal_fee_above_reserve"
    assert balance(home["org"])["available"] == D("35.50")


def test_changed_account_or_revoked_access_cancels_before_sending(home):
    paid(home)
    row = withdraw(home)
    home["destination"].enabled = False
    home["destination"].save()
    assert send(row) == []
    assert row.status == "cancelled" and row.issue == "withdrawal_no_longer_allowed"
    home["destination"].enabled = True
    home["destination"].save()
    second = withdraw(home)
    OrganizationMembership.objects.filter(user=home["manager"]).update(is_active=False)
    assert send(second) == []
    assert second.status == "cancelled"
    assert balance(home["org"])["available"] == D("97.50")


def test_waits_for_payouts_switch_and_a_fresh_matched_balance(home, settings):
    paid(home)
    row = withdraw(home)
    settings.LENCO_PAYOUTS_ENABLED = False
    assert send(row) == [] and row.status == "queued"
    settings.LENCO_PAYOUTS_ENABLED = True
    ProviderAccount.objects.update(checked_at=timezone.now() - timedelta(hours=1))
    assert send(row) == []
    assert row.status == "queued" and row.issue == "awaiting_balance_reconciliation"
    ProviderAccount.objects.update(checked_at=timezone.now())
    BalanceSnapshot.objects.create(
        account=ProviderAccount.objects.get(), status="matched", available_balance=60
    )
    assert send(row) == []  # 50 + 12 is more than Lenco holds
    BalanceSnapshot.objects.create(
        account=ProviderAccount.objects.get(), status="matched", available_balance=62
    )
    send(row, transfer(row))
    assert row.status == "successful"


def test_only_queued_withdrawals_can_be_cancelled(home):
    paid(home)
    row = withdraw(home)
    assert cancel_withdrawal(row).status == "cancelled"
    assert balance(home["org"])["available"] == D("97.50")
    second = withdraw(home)
    send(second, transfer(second, "pending"))
    with pytest.raises(Exception, match="already being sent"):
        cancel_withdrawal(second)


def test_unconfirmed_withdrawal_goes_to_review(home):
    paid(home)
    row = withdraw(home)
    send(row, transfer(row, "pending"))
    Withdrawal.objects.filter(pk=row.pk).update(submitted_at=timezone.now() - timedelta(days=4))
    assert send(row) == []
    assert row.status == "review" and row.issue == "withdrawal_unconfirmed"


def test_platform_totals_count_withdrawals(home):
    paid(home)
    row = withdraw(home)
    account = ProviderAccount.objects.get()
    assert landlord_totals(account)["held_for_landlords"] == D("97.50")
    send(row, transfer(row, "pending"))
    assert landlord_totals(account)["held_for_landlords"] == D("35.50")
    Withdrawal.objects.filter(pk=row.pk).update(next_check_at=timezone.now())
    send(row, transfer(row))
    totals = landlord_totals(account)
    assert totals["held_for_landlords"] == D("39.00")
    assert totals["payouts_total"] == D("50.00") and totals["payout_fees_total"] == D("8.50")


def test_transfer_webhook_wakes_the_withdrawal(home):
    from .testing import signature
    from .webhooks import receive_webhook

    paid(home)
    row = withdraw(home)
    send(row, transfer(row, "pending"))
    Withdrawal.objects.filter(pk=row.pk).update(next_check_at=None)
    body = json.dumps({"event": "transfer.successful", "data": {"reference": row.reference}})
    body = body.encode()
    receive_webhook(body, signature(body))
    receive_webhook(body, signature(body))
    row.refresh_from_db()
    assert row.next_check_at is not None
    assert row.exchange_set.filter(operation="webhook").count() == 1


def test_worker_processes_due_withdrawals(home):
    from .worker import run_cycle

    paid(home)
    row = withdraw(home)
    with patch("apps.payments.withdrawals.Provider") as provider:
        provider.return_value.request.return_value = transfer(row)
        with patch("apps.payments.services.Provider"):
            run_cycle()
    row.refresh_from_db()
    assert row.status == "successful"


def test_api_preview_request_list_and_cancel(home):
    paid(home)
    client = client_for(home["manager"])
    summary = client.get("/api/v1/payments/payouts/").json()["response_data"]
    assert summary["available"] == "97.50" and summary["largest"] == "85.50"
    assert summary["withdrawals_enabled"] is True and summary["destination"]["kind"]
    preview = client.post("/api/v1/payments/withdrawals/preview/", {"amount": "50"}).json()
    assert preview["response_data"] == {
        **preview["response_data"],
        "amount": "50.00",
        "fee": "12.00",
        "total": "62.00",
        "balance_after": "35.50",
    }
    key = str(uuid.uuid4())
    body = {"amount": "50.00", "fee": "12.00", "idempotency_key": key}
    created = client.post("/api/v1/payments/withdrawals/", body, format="json")
    assert created.status_code == 201
    again = client.post("/api/v1/payments/withdrawals/", body, format="json")
    assert again.json()["response_data"]["id"] == created.json()["response_data"]["id"]
    listing = client.get("/api/v1/payments/withdrawals/").json()
    assert listing["pagination"]["count"] == 1
    withdrawal_id = created.json()["response_data"]["id"]
    cancelled = client.post(f"/api/v1/payments/withdrawals/{withdrawal_id}/cancel/")
    assert cancelled.json()["response_data"]["status"] == "cancelled"


def test_api_access_is_limited_to_the_workspace_manager(home):
    from apps.organizations.models import Organization

    paid(home)
    row = withdraw(home)
    body = {"amount": "10.00", "fee": "12.00", "idempotency_key": str(uuid.uuid4())}
    for user in (home["tenant"], home["admin"]):
        client = client_for(user)
        assert client.post("/api/v1/payments/withdrawals/", body).status_code == 403
        assert (
            client.post(f"/api/v1/payments/withdrawals/{row.public_id}/cancel/").status_code == 403
        )
    assert client_for(home["tenant"]).get("/api/v1/payments/payouts/").status_code == 403
    other = Organization.objects.create(name="Other withdrawals workspace")
    from django.contrib.auth import get_user_model

    manager = get_user_model().objects.create_user(username="other-withdrawal-manager")
    OrganizationMembership.objects.create(organization=other, user=manager, role="landlord")
    client = client_for(manager)
    assert client.get("/api/v1/payments/withdrawals/").json()["pagination"]["count"] == 0
    assert client.post(f"/api/v1/payments/withdrawals/{row.public_id}/cancel/").status_code == 404
    assert client.get("/api/v1/payments/payouts/").json()["response_data"]["available"] == "0.00"


@pytest.mark.django_db(transaction=True)
def test_concurrent_withdrawals_cannot_spend_one_balance_on_postgres(home):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks")
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections

    paid(home)

    def attempt(_):
        close_old_connections()
        try:
            withdraw(home, amount="60.00")
            return True
        except Exception:
            return False
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, [1, 2]))
    assert sorted(results) == [False, True]
    assert Withdrawal.objects.count() == 1


def test_manager_is_alerted_about_delivered_and_failed_withdrawals(home):
    paid(home)
    delivered = withdraw(home, amount="20.00")
    send(delivered, transfer(delivered))
    failed = withdraw(home, amount="20.00")
    send(failed, transfer(failed, "failed", id="provider-transfer-2"))
    alerts = client_for(home["manager"]).get("/api/v1/notifications/").json()["response_data"]
    titles = {
        item["id"].rsplit(":", 1)[1]: item["title"]
        for item in alerts["items"]
        if item["id"].startswith("withdrawal:")
    }
    assert titles == {
        "successful": "Withdrawal delivered",
        "failed": "Withdrawal failed · returned to your balance",
    }


def test_platform_admin_sees_withdrawal_details_and_evidence(home):
    paid(home)
    row = withdraw(home)
    with patch("apps.payments.provider.urllib.request.build_opener") as opener:
        opener.return_value.open.side_effect = OSError("offline")
        process_withdrawal(row)
    admin = client_for(home["admin"])
    detail = admin.get(f"/api/v1/payments/platform/withdrawals/{row.public_id}/").json()
    assert detail["response_data"]["workspace"] == home["org"].name
    evidence = admin.get(f"/api/v1/payments/platform/collections/{row.public_id}/exchanges/")
    assert [item["operation"] for item in evidence.json()["response_data"]] == ["withdrawal_submit"]
    manager = client_for(home["manager"])
    assert manager.get(f"/api/v1/payments/platform/withdrawals/{row.public_id}/").status_code == 403
