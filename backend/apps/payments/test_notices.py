"""Explicit payment notices: right audience, once per transition, never blocking money."""

import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from apps.notifications.models import OperationalDelivery
from apps.organizations.models import OrganizationMembership

from .models import Collection, Withdrawal
from .provider import ProviderResult
from .services import process_payout, reconcile_collection
from .testing import ACCOUNT, checkout, collection_result, paid, payout_result
from .withdrawals import cancel_withdrawal, process_withdrawal, request_withdrawal

pytestmark = pytest.mark.django_db


@pytest.fixture
def emails(home):
    tenant = home["invoice"].tenant
    tenant.email = "tenant@example.com"
    tenant.save(update_fields=["email"])
    co = get_user_model().objects.create_user(username="co-manager", email="co@example.com")
    OrganizationMembership.objects.create(organization=home["org"], user=co, role="landlord")
    home["co"] = co
    return home


def notices(prefix):
    return sorted(
        (row.event, row.audience, row.recipient)
        for row in OperationalDelivery.objects.filter(event__startswith=prefix)
    )


def reconcile(row, result):
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = result
        reconcile_collection(row)
    row.refresh_from_db()


def test_failed_attempt_tells_only_the_tenant_once(emails):
    row = checkout(emails)
    reconcile(row, collection_result(row, state="failed"))
    reconcile(row, collection_result(row, state="failed"))
    assert row.status == "failed"
    assert notices("collection.") == [("collection.failed", "tenant", "tenant@example.com")]


def test_review_goes_to_managers_not_the_tenant(emails):
    row = checkout(emails)
    reconcile(row, collection_result(row, amount="99.00"))
    assert row.status == "review"
    assert notices("collection.") == [
        ("collection.review", "manager", "co@example.com"),
        ("collection.review", "manager", "manager@example.com"),
    ]


def test_success_is_announced_by_the_receipt_not_a_collection_notice(emails):
    row = paid(emails)
    assert row.status == "successful"
    assert notices("collection.") == []
    assert ("payment.confirmed", "tenant", "tenant@example.com") in notices("payment.")


def test_payout_outcome_reaches_managers_only(emails):
    row = paid(emails)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = payout_result(row.payout)
        process_payout(row.payout)
    row.payout.refresh_from_db()
    assert row.payout.status == "successful"
    assert notices("payout.") == [
        ("payout.successful", "manager", "co@example.com"),
        ("payout.successful", "manager", "manager@example.com"),
    ]


def withdraw(home):
    return request_withdrawal(
        organization=home["org"], user=home["manager"], amount="50.00", fee="12.00",
        idempotency_key=uuid.uuid4(),
    )


def transfer(row, state):
    return ProviderResult({"status": True, "data": {
        "id": "provider-transfer-1", "reference": row.reference, "amount": str(row.amount),
        "currency": "ZMW", "accountId": ACCOUNT, "status": state, "fee": "8.50",
        "creditAccount": {"type": "mobile-money", "phone": "0971111111", "operator": "airtel"},
    }}, 200)


def test_withdrawal_request_skips_requester_and_pending_is_quiet(emails, settings):
    settings.LENCO_AUTOMATIC_PAYOUTS = False
    paid(emails)
    row = withdraw(emails)
    assert notices("withdrawal.") == [("withdrawal.queued", "manager", "co@example.com")]
    with patch("apps.payments.withdrawals.Provider") as provider:
        provider.return_value.request.side_effect = [transfer(row, "pending")]
        process_withdrawal(row)
    row.refresh_from_db()
    assert row.status == "pending"
    assert [e for e, _, _ in notices("withdrawal.")] == ["withdrawal.queued"]
    with patch("apps.payments.withdrawals.Provider") as provider:
        provider.return_value.request.side_effect = [transfer(row, "successful")]
        process_withdrawal(row)
    row.refresh_from_db()
    assert row.status == "successful"
    assert ("withdrawal.successful", "manager", "manager@example.com") in notices("withdrawal.")
    assert ("withdrawal.successful", "manager", "co@example.com") in notices("withdrawal.")


def test_cancelled_withdrawal_tells_co_managers(emails, settings):
    settings.LENCO_AUTOMATIC_PAYOUTS = False
    paid(emails)
    row = cancel_withdrawal(withdraw(emails))
    assert row.status == Withdrawal.Status.CANCELLED
    assert ("withdrawal.cancelled", "manager", "co@example.com") in notices("withdrawal.")


def test_broken_notice_queue_never_undoes_a_collection_outcome(emails):
    row = checkout(emails)
    with patch("apps.notifications.events.enqueue", side_effect=RuntimeError("broken")):
        reconcile(row, collection_result(row, state="failed"))
    assert Collection.objects.get(pk=row.pk).status == "failed"
    assert notices("collection.") == []


def test_broken_notice_queue_never_undoes_a_withdrawal(emails, settings):
    settings.LENCO_AUTOMATIC_PAYOUTS = False
    paid(emails)
    with patch("apps.notifications.events.enqueue", side_effect=RuntimeError("broken")):
        row = withdraw(emails)
    assert Withdrawal.objects.get(pk=row.pk).amount == Decimal("50.00")
