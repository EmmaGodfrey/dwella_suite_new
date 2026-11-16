"""A paid checkout is confirmed seconds after Lenco says so, never sooner."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Payment

from . import wake
from .models import Collection
from .schedule import WEBHOOK_RECHECK
from .services import reconcile_collection
from .testing import checkout, client_for, collection_result, signature, webhook_body

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_wake():
    cache.delete(wake.WAKE_KEY)
    yield
    cache.delete(wake.WAKE_KEY)


def post_webhook(row):
    raw = webhook_body(row)
    return APIClient().post(
        "/api/v1/payments/webhook/",
        raw,
        content_type="application/json",
        HTTP_X_LENCO_SIGNATURE=signature(raw),
    )


def test_signed_webhook_wakes_the_worker_after_commit(home, django_capture_on_commit_callbacks):
    row = checkout(home)
    with django_capture_on_commit_callbacks(execute=True):
        assert post_webhook(row).status_code == 200
    assert cache.get(wake.WAKE_KEY)
    # The nudge is consumed once and carries nothing else.
    assert wake.wait(1, []) is True
    assert cache.get(wake.WAKE_KEY) is None


def test_unsigned_webhook_never_wakes_the_worker(home, django_capture_on_commit_callbacks):
    row = checkout(home)
    raw = webhook_body(row)
    with django_capture_on_commit_callbacks(execute=True):
        response = APIClient().post(
            "/api/v1/payments/webhook/",
            raw,
            content_type="application/json",
            HTTP_X_LENCO_SIGNATURE="0" * 128,
        )
    assert response.status_code in (401, 403)
    assert cache.get(wake.WAKE_KEY) is None


def test_idle_wait_returns_without_a_nudge_or_when_stopping():
    assert wake.wait(0.3, []) is False
    assert wake.wait(5, [True]) is False


def test_status_lagging_the_webhook_is_asked_again_within_seconds(home):
    row = checkout(home)
    post_webhook(row)
    row.refresh_from_db()
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(
            row, state="pending", settled=False
        )
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.status == "pending" and not Payment.objects.exists()
    assert row.next_check_at - row.last_checked_at <= WEBHOOK_RECHECK


def test_quick_rechecks_stop_a_minute_after_the_webhook(home):
    row = checkout(home)
    post_webhook(row)
    old = (timezone.now() - timedelta(minutes=2)).isoformat()
    Collection.objects.filter(pk=row.pk).update(provider_state={"webhook_at": old})
    row.refresh_from_db()
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(
            row, state="pending", settled=False
        )
        reconcile_collection(row)
    row.refresh_from_db()
    assert row.next_check_at - row.last_checked_at > timedelta(seconds=10)


def test_tenant_status_request_wakes_only_for_an_open_checkout(
    home, django_capture_on_commit_callbacks
):
    row = checkout(home)
    client = client_for(home["tenant"])
    url = f"/api/v1/payments/tenant/collections/{row.public_id}/"
    with django_capture_on_commit_callbacks(execute=True):
        assert client.post(url).status_code == 202
    assert wake.wait(1, []) is True
    Collection.objects.filter(pk=row.pk).update(status="failed")
    with django_capture_on_commit_callbacks(execute=True):
        client.post(url)
    assert cache.get(wake.WAKE_KEY) is None


def test_idle_pause_ends_when_the_next_collection_is_due(home):
    from .worker import idle_seconds

    row = checkout(home)
    Collection.objects.filter(pk=row.pk).update(next_check_at=timezone.now() + WEBHOOK_RECHECK)
    assert 2 < idle_seconds(5) <= 3
    Collection.objects.filter(pk=row.pk).update(next_check_at=timezone.now() - timedelta(seconds=1))
    # Overdue: a short floor, never a busy spin.
    assert idle_seconds(5) == 0.25
    Collection.objects.filter(pk=row.pk).update(next_check_at=None)
    assert idle_seconds(5) == 5


def test_worker_runs_a_three_second_recheck_without_waiting_out_its_pause(home):
    """The real worker loop, timed: no nudge, a row due in about one second."""
    import time

    from django.core.management import call_command

    from .management.commands import run_payments_worker as command

    row = checkout(home)
    Collection.objects.filter(pk=row.pk).update(
        next_check_at=timezone.now() + timedelta(seconds=1)
    )
    calls = []

    def cycle():
        calls.append(time.monotonic())
        if len(calls) == 2:
            raise KeyboardInterrupt  # end the loop; Exception would be swallowed
        return 0

    cache.delete(command.LOCK_KEY)
    try:
        with (
            patch.object(command, "run_cycle", cycle),
            patch.object(command, "balance_configured", return_value=False),
            # The test's own transaction would otherwise be closed under it.
            patch.object(command, "close_old_connections"),
            patch.object(command.logger, "exception", side_effect=AssertionError),
            pytest.raises(KeyboardInterrupt),
        ):
            call_command("run_payments_worker")
    finally:
        cache.delete(command.LOCK_KEY)
    # Before this fix the second pass came after the full five-second pause.
    assert calls[1] - calls[0] < 2
