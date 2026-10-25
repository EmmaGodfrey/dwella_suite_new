import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.billing.models import Invoice, Payment
from apps.billing.services import (
    generate_rent_invoices,
    record_payment,
    reverse_payment,
    void_invoice,
)
from apps.billing.tests import THIS_MONTH, make_lease
from apps.organizations.models import Organization
from apps.subscriptions.models import WorkspaceAccessPolicy

from .models import Collection, Destination, Payout
from .provider import ProviderResult
from .services import process_payout, reconcile_collection
from .testing import checkout, collection_result, paid, payout_result

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity", "0.001", "4000"])
def test_checkout_rejects_bad_amounts(home, amount):
    with pytest.raises(ValidationError):
        checkout(home, amount=amount)
    assert not Collection.objects.exists()


def test_idempotency_rejects_changed_details_and_resume_does_not_duplicate(home):
    key = uuid.uuid4()
    first = checkout(home, key=key)
    assert checkout(home).pk == first.pk
    with pytest.raises(ValidationError):
        checkout(home, key=key, amount="110")
    assert Collection.objects.count() == 1


def test_disabled_feature_destination_and_currency_block_checkout(home, settings):
    settings.LENCO_PAYMENTS_ENABLED = False
    with pytest.raises(ValidationError):
        checkout(home)
    settings.LENCO_PAYMENTS_ENABLED = True
    policy = WorkspaceAccessPolicy.objects.create(
        organization=home["org"], feature_overrides={"online_payments": False}
    )
    from rest_framework.exceptions import PermissionDenied

    with pytest.raises(PermissionDenied):
        checkout(home)
    policy.delete()
    home["destination"].enabled = False
    home["destination"].save()
    with pytest.raises(ValidationError):
        checkout(home)
    home["destination"].enabled = True
    home["destination"].save()
    home["org"].currency = "USD"
    home["org"].save()
    with pytest.raises(ValidationError):
        checkout(home)


def test_success_updates_existing_invoice_receipt_and_no_duplicate_credit(home):
    row = paid(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        reconcile_collection(row)
    assert Payment.objects.count() == 1
    assert Payout.objects.count() == 1
    home["invoice"].refresh_from_db()
    assert home["invoice"].amount_paid == Decimal("100.00")
    assert home["invoice"].status == "partially_paid"
    assert row.payment.receipt_number.startswith("RCT")
    assert row.payout.amount == Decimal("97.50")
    with pytest.raises(ValidationError, match="provider reconciliation"):
        reverse_payment(row.payment, reason="Should not be reversed manually", user=home["manager"])


def test_unsettled_success_records_rent_but_waits_before_payout(home):
    row = paid(home, settled=False)
    assert row.status == "successful" and row.payment_id
    assert not Payout.objects.exists()
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        reconcile_collection(row)
    assert Payout.objects.count() == 1


@pytest.mark.parametrize(
    "overrides",
    [{"amount": "101"}, {"currency": "USD"}, {"reference": "wrong"}, {"id": ""}, {"amount": "NaN"}],
)
def test_mismatched_collections_never_credit_or_pay_out(home, overrides):
    row = checkout(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row, **overrides)
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.status == "review"
    assert not Payment.objects.exists() and not Payout.objects.exists()


def test_duplicate_provider_id_does_not_credit_another_invoice(home):
    paid(home)
    other_lease = make_lease(home["org"], unit_name="2B", phone="+260971111112")
    generate_rent_invoices(home["org"], THIS_MONTH)
    home["invoice"] = Invoice.objects.get(tenant=other_lease.tenant)
    row = checkout(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.status == "review" and row.issue == "duplicate_provider_collection"
    assert Payment.objects.count() == 1


@pytest.mark.parametrize("race", ["manual", "void"])
def test_received_money_is_preserved_as_exception_if_invoice_changed(home, race):
    row = checkout(home)
    if race == "void":
        void_invoice(home["invoice"])
    else:
        record_payment(
            invoice=home["invoice"],
            amount=Decimal("3900"),
            method="cash",
            paid_on=timezone.localdate(),
        )
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.provider_id and row.issue == "received_money_needs_allocation"
    assert row.status == "review" and not row.payment_id
    assert not Payout.objects.exists()


def test_stale_failure_does_not_undo_payment(home):
    row = paid(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(
            row, state="failed", settled=False
        )
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.status == "successful" and row.settled and row.payment_id
    assert Payment.objects.count() == 1


def test_payout_is_submitted_once_and_updates_separate_status(home):
    row = paid(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = payout_result(row.payout)
        process_payout(row.payout)
        process_payout(row.payout)
        assert provider.return_value.request.call_count == 1
        call = provider.return_value.request.call_args
        assert call.args == ("payout_submit",)
        assert call.kwargs["payload"]["phone"] == home["destination"].phone
        assert call.kwargs["payload"]["amount"] == 97.5
    row.payout.refresh_from_db()
    assert row.payout.status == "successful"
    assert row.payout.fee == Decimal("1.00")
    assert row.status == "successful"


def test_payout_timeout_is_polled_without_reposting(home):
    row = paid(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = ProviderResult({}, None, "network_error")
        process_payout(row.payout)
        row.payout.refresh_from_db()
        assert row.payout.status == "submitting"
        provider.return_value.request.return_value = payout_result(row.payout)
        process_payout(row.payout)
        assert [call.args[0] for call in provider.return_value.request.call_args_list] == [
            "payout_submit",
            "payout_status",
        ]


@pytest.mark.parametrize("change", ["disabled", "destination", "settlement", "suspended"])
def test_payout_cannot_debit_when_guard_fails(home, settings, change):
    row = paid(home)
    if change == "disabled":
        settings.LENCO_PAYOUTS_ENABLED = False
    elif change == "destination":
        Destination.objects.filter(pk=row.destination_id).update(enabled=False)
    elif change == "settlement":
        Collection.objects.filter(pk=row.pk).update(settled=False)
    else:
        Organization.objects.filter(pk=row.organization_id).update(is_active=False)
    with patch("apps.payments.services.Provider") as provider:
        process_payout(row.payout)
        provider.assert_not_called()


def test_payout_mismatch_never_marks_delivered(home):
    row = paid(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = payout_result(row.payout, amount="99")
        process_payout(row.payout)
    row.payout.refresh_from_db()
    assert row.payout.status == "review" and row.payout.issue == "payout_details_mismatch"


def test_payout_failure_does_not_reopen_tenant_invoice(home):
    row = paid(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = payout_result(row.payout, state="failed")
        process_payout(row.payout)
    row.payout.refresh_from_db()
    assert row.payout.status == "failed"
    home["invoice"].refresh_from_db()
    assert home["invoice"].amount_paid == row.amount


@pytest.mark.django_db(transaction=True)
def test_concurrent_checkout_and_payout_debit_once_on_postgres(home):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks")
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock

    from django.db import close_old_connections

    key = uuid.uuid4()

    def start(_):
        close_old_connections()
        try:
            return checkout(home, key=key).pk
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(start, [1, 2]))
    assert len(set(ids)) == 1 and Collection.objects.count() == 1
    row = Collection.objects.get()
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        reconcile_collection(row)
    payout = Payout.objects.get()
    calls = []
    guard = Lock()

    def respond(operation, **kwargs):
        assert not connection.in_atomic_block
        with guard:
            calls.append(operation)
        return payout_result(payout)

    def send(_):
        close_old_connections()
        try:
            process_payout(payout)
        finally:
            connection.close()

    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.side_effect = respond
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(send, [1, 2]))
    assert calls.count("payout_submit") == 1
    payout.refresh_from_db()
    assert payout.status == "successful"


@pytest.mark.parametrize("state", ["missing", "mismatch", "stale", "insufficient"])
def test_payout_waits_for_fresh_matching_funded_balance(home, state):
    from datetime import timedelta

    from .models import BalanceSnapshot, ProviderAccount

    row = paid(home)
    account = ProviderAccount.objects.get()
    if state == "missing":
        # Preserve immutable history; select a different debit account instead.
        Collection.objects.filter(pk=row.pk).update(
            debit_account_id="00000000-0000-0000-0000-000000000002"
        )
    else:
        BalanceSnapshot.objects.create(
            account=account,
            available_balance=0 if state == "insufficient" else 100000,
            ledger_balance=100000,
            status="mismatch" if state == "mismatch" else "matched",
        )
        if state == "stale":
            with patch(
                "apps.payments.balances.timezone.now",
                return_value=timezone.now() + timedelta(minutes=7),
            ):
                with patch("apps.payments.services.Provider") as provider:
                    process_payout(row.payout)
                    provider.assert_not_called()
            return
    with patch("apps.payments.services.Provider") as provider:
        process_payout(row.payout)
        provider.assert_not_called()
    row.payout.refresh_from_db()
    assert row.payout.status in {"queued", "review"}


@pytest.mark.django_db(transaction=True)
def test_distinct_payouts_cannot_concurrently_reserve_the_same_balance(home):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL account reservation lock")
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections

    from .models import BalanceSnapshot, ProviderAccount

    paid(home)
    second = checkout(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(
            second, id="provider-collection-2"
        )
        reconcile_collection(second)
    BalanceSnapshot.objects.create(
        account=ProviderAccount.objects.get(),
        status="matched",
        available_balance=100,
        ledger_balance=100,
    )
    payouts = list(Payout.objects.order_by("pk"))

    def send(row):
        close_old_connections()
        try:
            process_payout(row)
        finally:
            connection.close()

    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.side_effect = lambda operation, **kwargs: payout_result(
            kwargs["payout"]
        )
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(send, payouts))
        assert provider.return_value.request.call_count == 1
    assert Payout.objects.filter(status="successful").count() == 1
    assert (
        Payout.objects.filter(status="queued", issue="awaiting_balance_reconciliation").count() == 1
    )
