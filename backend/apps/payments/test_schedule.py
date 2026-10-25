from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Payment

from .models import Collection, Exchange, Payout
from .provider import ProviderResult
from .services import process_payout, reconcile_collection
from .testing import (
    checkout,
    client_for,
    collection_result,
    http_response,
    paid,
    payout_result,
    signature,
    webhook_body,
)
from .worker import run_cycle

pytestmark = pytest.mark.django_db
NOT_FOUND = ProviderResult(
    {"status": False, "message": "Payment details was not found", "data": None}, 404, "http_error"
)


def age(row, **delta):
    """Pretend the row was created that long ago."""
    type(row).objects.filter(pk=row.pk).update(created_at=timezone.now() - timedelta(**delta))
    row.refresh_from_db()


def reconcile(row, result):
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = result
        reconcile_collection(row)
    row.refresh_from_db()
    return row


def test_checks_slow_down_then_an_unpaid_checkout_expires_and_frees_the_invoice(home):
    row = checkout(home)
    assert row.next_check_at > timezone.now()
    reconcile(row, NOT_FOUND)
    assert row.status == "pending"
    assert row.next_check_at - row.last_checked_at == timedelta(seconds=30)
    age(row, minutes=10)
    reconcile(row, NOT_FOUND)
    assert row.next_check_at - row.last_checked_at == timedelta(minutes=2)
    age(row, minutes=31)
    reconcile(row, NOT_FOUND)
    assert row.status == "expired" and row.issue == "checkout_not_completed"
    # The invoice is free for a new checkout straight away.
    assert checkout(home).status == "pending"


def test_a_checkout_still_pending_at_lenco_after_the_window_expires(home):
    row = checkout(home)
    age(row, minutes=31)
    reconcile(row, collection_result(row, state="pending", settled=False))
    assert row.status == "expired"
    assert row.provider_state["status"] == "pending"


def test_network_trouble_never_expires_a_checkout(home):
    row = checkout(home)
    age(row, minutes=31)
    reconcile(row, ProviderResult({}, None, "network_error"))
    assert row.status == "pending" and row.issue == "network_error"
    assert row.next_check_at - row.last_checked_at == timedelta(minutes=15)


def test_late_approval_after_expiry_is_still_recorded_on_the_day_it_was_paid(home):
    row = checkout(home)
    age(row, minutes=31)
    reconcile(row, NOT_FOUND)
    assert row.status == "expired" and row.next_check_at
    paid_at = (timezone.now() - timedelta(minutes=20)).isoformat()
    reconcile(row, collection_result(row, settled=False, completedAt=paid_at))
    assert row.status == "successful"
    payment = Payment.objects.get()
    assert payment.paid_on == timezone.localdate(timezone.now() - timedelta(minutes=20))


def test_receipt_uses_lencos_completion_date_not_the_check_date(home):
    row = checkout(home)
    reconcile(row, collection_result(row, completedAt="2026-10-20T08:00:00Z"))
    assert Payment.objects.get().paid_on == date(2026, 10, 20)
    assert row.provider_state["completed_at"].startswith("2026-10-20T08:00")


def test_a_future_completion_date_falls_back_to_today(home):
    row = checkout(home)
    future = (timezone.now() + timedelta(days=3)).isoformat()
    reconcile(row, collection_result(row, completedAt=future))
    assert Payment.objects.get().paid_on == timezone.localdate()


def test_expired_safety_checks_stop_after_a_day(home):
    row = checkout(home)
    age(row, minutes=31)
    reconcile(row, NOT_FOUND)
    assert row.next_check_at - row.last_checked_at == timedelta(minutes=15)
    age(row, hours=5)
    reconcile(row, NOT_FOUND)
    assert row.next_check_at - row.last_checked_at == timedelta(hours=2)
    age(row, days=2)
    reconcile(row, NOT_FOUND)
    assert row.next_check_at is None


def test_repeated_polls_store_one_answer(home):
    row = checkout(home)
    for _ in range(5):
        with patch("apps.payments.provider.urllib.request.build_opener") as build:
            build.return_value.open.return_value = http_response(
                b'{"status":true,"data":{"status":"pending"}}'
            )
            reconcile_collection(row)
    assert Exchange.objects.filter(operation="collection_status").count() == 1


def test_worker_only_reads_rows_that_are_due(home):
    finished = paid(home)
    assert finished.next_check_at is None
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = payout_result(finished.payout, "pending")
        assert run_cycle() == 1  # only the settled collection's queued payout
        provider.return_value.request.assert_called_once()
        assert provider.return_value.request.call_args.args[0] == "payout_submit"


def test_webhook_revives_an_expired_checkout_and_extends_its_window(home):
    row = checkout(home)
    age(row, minutes=40)
    reconcile(row, NOT_FOUND)
    assert row.status == "expired"
    body = webhook_body(row)
    APIClient().post(
        "/api/v1/payments/webhook/",
        body,
        content_type="application/json",
        HTTP_X_LENCO_SIGNATURE=signature(body),
    )
    row.refresh_from_db()
    assert row.provider_state["webhook_at"] and row.next_check_at <= timezone.now()
    reconcile(row, collection_result(row, state="pending", settled=False))
    # Within the webhook's window: watched closely again, not given up.
    assert row.next_check_at - row.last_checked_at == timedelta(minutes=2)


def test_tenant_check_request_only_touches_rows_that_can_change(home):
    finished = paid(home)
    client = client_for(home["tenant"])
    url = f"/api/v1/payments/tenant/collections/{finished.public_id}/"
    assert client.post(url).status_code == 202
    finished.refresh_from_db()
    assert finished.next_check_at is None
    Collection.objects.filter(pk=finished.pk).update(status="pending", settled=False)
    client.post(url)
    finished.refresh_from_db()
    assert finished.next_check_at <= timezone.now()


def test_payouts_wait_quietly_while_disabled(home, settings):
    settings.LENCO_PAYOUTS_ENABLED = False
    payout = paid(home).payout
    with patch("apps.payments.services.Provider") as provider:
        process_payout(payout)
        provider.assert_not_called()
    payout.refresh_from_db()
    assert payout.status == "queued"
    assert payout.next_check_at - timezone.now() > timedelta(minutes=14)


def test_unconfirmed_payout_goes_to_review_after_three_days(home):
    payout = paid(home).payout
    Payout.objects.filter(pk=payout.pk).update(
        status="pending", submitted_at=timezone.now() - timedelta(days=4)
    )
    with patch("apps.payments.services.Provider") as provider:
        process_payout(payout)
        provider.assert_not_called()
    payout.refresh_from_db()
    assert payout.status == "review" and payout.issue == "payout_unconfirmed"
    assert payout.next_check_at is None


def test_one_broken_row_is_deferred_without_blocking_the_rest(home):
    broken = checkout(home)
    Collection.objects.filter(pk=broken.pk).update(status="failed")  # frees the invoice
    healthy = checkout(home, amount="50.00")
    Collection.objects.update(next_check_at=timezone.now())
    calls = []

    def check(row):
        calls.append(row.pk)
        if row.pk == broken.pk:
            raise RuntimeError("unexpected provider shape")

    with patch("apps.payments.worker.reconcile_collection", side_effect=check):
        run_cycle()
    assert set(calls) == {broken.pk, healthy.pk}
    broken.refresh_from_db()
    assert broken.next_check_at - timezone.now() > timedelta(minutes=14)
