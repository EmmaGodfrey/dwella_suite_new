import logging
from datetime import timedelta
from time import monotonic

from django.conf import settings
from django.utils import timezone

from .models import Collection, Payout, Withdrawal
from .payout_plans import run_due_plans
from .services import process_payout, reconcile_collection
from .withdrawals import process_withdrawal

CYCLE_SECONDS = 25
logger = logging.getLogger(__name__)


def _check(handler, row):
    """One row; an unexpected error defers only that row, never the queue."""
    try:
        handler(row)
    except Exception:
        logger.exception("Payment check failed for %s", row.reference)
        later = timezone.now() + timedelta(minutes=15)
        type(row).objects.filter(pk=row.pk).update(next_check_at=later)


def run_cycle(limit=50):
    """Check every collection, payout and withdrawal that is due, oldest first,
    after starting the withdrawals of due payout timings.

    One indexed query per kind picks the due rows; rows that cannot change
    have no next check and are never read. Never starts a collection and
    never retries a debit.
    """
    environment = settings.LENCO_ENVIRONMENT
    deadline = monotonic() + CYCLE_SECONDS
    now = timezone.now()
    count = 0
    collections = Collection.objects.filter(
        environment=environment, next_check_at__lte=now
    ).order_by("next_check_at")[:limit]
    for row in collections:
        if monotonic() > deadline:
            return count
        _check(reconcile_collection, row)
        count += 1
    payouts = (
        Payout.objects.filter(collection__environment=environment, next_check_at__lte=now)
        .select_related("collection")
        .order_by("next_check_at")[:limit]
    )
    for row in payouts:
        if monotonic() > deadline:
            return count
        _check(process_payout, row)
        count += 1
    # Due payout timings queue their withdrawals for the loop below.
    count += run_due_plans(now)
    withdrawals = Withdrawal.objects.filter(
        environment=environment, next_check_at__lte=now
    ).order_by("next_check_at")[:limit]
    for row in withdrawals:
        if monotonic() > deadline:
            return count
        _check(process_withdrawal, row)
        count += 1
    return count


def idle_seconds(longest, shortest=0.25):
    """How long the idle worker may pause before the next collection is due.

    A checkout rechecked seconds after its webhook must not wait out the
    whole idle pause. One read of the partial next-check index; payouts and
    withdrawals are checked no faster than every thirty seconds, so the
    normal pause already suits them.
    """
    due = (
        Collection.objects.filter(
            environment=settings.LENCO_ENVIRONMENT, next_check_at__isnull=False
        )
        .order_by("next_check_at")
        .values_list("next_check_at", flat=True)
        .first()
    )
    if due is None:
        return longest
    wait = (due - timezone.now()).total_seconds()
    return min(longest, max(shortest, wait))
