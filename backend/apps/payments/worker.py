import logging
from datetime import timedelta
from time import monotonic

from django.conf import settings
from django.utils import timezone

from .models import Collection, Payout
from .services import process_payout, reconcile_collection

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
    """Check every collection and payout that is due, oldest first.

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
    return count
