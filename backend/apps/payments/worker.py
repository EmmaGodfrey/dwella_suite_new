from datetime import timedelta
from time import monotonic

from django.conf import settings
from django.db.models import F, Q
from django.utils import timezone

from .models import Collection, Payout, WebhookReceipt
from .services import process_payout, reconcile_collection


def run_cycle(limit=20):
    """Webhook wakeups plus polling; never submits a collection or retries a debit."""
    environment = settings.LENCO_ENVIRONMENT
    count = 0
    deadline = monotonic() + 25
    due = timezone.now() - timedelta(seconds=30)
    receipts = WebhookReceipt.objects.filter(environment=environment, processed_at=None).filter(
        Q(last_attempt_at=None) | Q(last_attempt_at__lt=due)
    )
    for receipt in receipts.order_by(F("last_attempt_at").asc(nulls_first=True), "created_at")[
        :limit
    ]:
        if monotonic() > deadline:
            return count
        WebhookReceipt.objects.filter(pk=receipt.pk).update(last_attempt_at=timezone.now())
        processed = True
        if receipt.event.startswith("collection."):
            row = Collection.objects.filter(
                environment=environment, reference=receipt.reference
            ).first()
            if row:
                processed = reconcile_collection(row)
                row.refresh_from_db()
                if receipt.event == "collection.successful" and row.status not in {
                    "successful",
                    "review",
                }:
                    processed = False
                if (
                    receipt.event == "collection.settled"
                    and not row.settled
                    and row.issue != "settlement_details_mismatch"
                ):
                    processed = False
        else:
            payout = Payout.objects.filter(
                collection__environment=environment, reference=receipt.reference
            ).first()
            if payout and payout.status != "queued":
                # A late success can correct a previously failed payout, but a
                # webhook is only a wakeup: always fetch the authoritative status.
                from .provider import Provider
                from .services import _apply_payout_result

                result = Provider(environment).request(
                    "payout_status", collection=payout.collection, payout=payout
                )
                processed = _apply_payout_result(payout, result)
                payout.refresh_from_db()
                if receipt.event == "transfer.successful" and payout.status not in {
                    "successful",
                    "review",
                }:
                    processed = False
        if processed:
            WebhookReceipt.objects.filter(pk=receipt.pk).update(processed_at=timezone.now())
        count += 1
    due = timezone.now() - timedelta(seconds=30)
    collections = Collection.objects.filter(environment=environment).filter(
        Q(last_checked_at=None)
        | Q(status__in=["pending", "successful"], settled=False, last_checked_at__lt=due)
    )
    for row in collections.order_by(F("last_checked_at").asc(nulls_first=True), "created_at")[
        :limit
    ]:
        if monotonic() > deadline:
            return count
        reconcile_collection(row)
        count += 1
    payouts = Payout.objects.filter(collection__environment=environment).filter(
        Q(status="queued") | Q(status__in=["submitting", "pending"], last_checked_at__lt=due)
    )
    for row in payouts.order_by(F("last_checked_at").asc(nulls_first=True), "created_at")[:limit]:
        if monotonic() > deadline:
            return count
        process_payout(row)
        count += 1
    return count
