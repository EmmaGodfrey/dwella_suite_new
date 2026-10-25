from time import monotonic

from django.conf import settings
from django.utils import timezone

from .models import Collection, Payout
from .services import process_payout, reconcile_collection

CYCLE_SECONDS = 25


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
        reconcile_collection(row)
        count += 1
    payouts = (
        Payout.objects.filter(collection__environment=environment, next_check_at__lte=now)
        .select_related("collection")
        .order_by("next_check_at")[:limit]
    )
    for row in payouts:
        if monotonic() > deadline:
            return count
        process_payout(row)
        count += 1
    return count
