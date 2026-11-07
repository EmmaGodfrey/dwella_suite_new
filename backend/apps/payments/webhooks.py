import hashlib
import hmac
import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .evidence import record_exchange, strict_json
from .models import Collection, Exchange, Payout, Withdrawal
from .schedule import stamp

MAX_WEBHOOK = 128 * 1024
EVENTS = {
    "collection.successful",
    "collection.failed",
    "collection.settled",
    "transfer.successful",
    "transfer.failed",
}


def receive_webhook(body, signature):
    """Keep a verified webhook as evidence and ask Lenco about its row now.

    A webhook is never evidence of payment by itself; the worker always fetches
    the authoritative status. A repeated delivery of the same body is ignored.
    """
    if len(body) > MAX_WEBHOOK:
        raise ValidationError("Webhook exceeds the size limit.")
    secret = settings.LENCO_SECRET_KEY
    if not secret or not re.fullmatch(r"[a-fA-F0-9]{128}", signature or ""):
        raise PermissionDenied("Invalid webhook signature.")
    key = hashlib.sha256(secret.encode()).hexdigest().encode()
    expected = hmac.new(key, body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(expected, signature.lower()):
        raise PermissionDenied("Invalid webhook signature.")
    try:
        payload = strict_json(body)
    except (ValueError, UnicodeError, RecursionError):
        raise ValidationError("Invalid webhook JSON.") from None
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise ValidationError("Invalid webhook payload.")
    event = payload.get("event")
    if not isinstance(event, str):
        raise ValidationError("Invalid webhook event.")
    if event not in EVENTS:
        return
    reference = payload["data"].get("reference")
    if not isinstance(reference, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,50}", reference):
        raise ValidationError("Invalid webhook reference.")
    environment = settings.LENCO_ENVIRONMENT
    with transaction.atomic():
        # Locking the row serialises duplicate deliveries.
        payout = withdrawal = None
        if event.startswith("collection."):
            row = collection = (
                Collection.objects.select_for_update()
                .filter(reference=reference, environment=environment)
                .first()
            )
        else:
            row = payout = (
                Payout.objects.select_for_update(of=("self",))
                .select_related("collection")
                .filter(reference=reference, collection__environment=environment)
                .first()
            )
            collection = payout.collection if payout else None
            if payout is None:
                row = withdrawal = (
                    Withdrawal.objects.select_for_update()
                    .filter(reference=reference, environment=environment)
                    .first()
                )
        # Other activity in this merchant account is outside Dwella's rent flow.
        if row is None:
            return
        digest = hashlib.sha256(body).hexdigest()
        if Exchange.objects.filter(
            collection=collection, withdrawal=withdrawal, operation="webhook", body_sha256=digest
        ).exists():
            return
        record_exchange(
            environment=environment,
            operation="webhook",
            body=body,
            collection=collection,
            payout=payout,
            withdrawal=withdrawal,
        )
        now = timezone.now()
        row.next_check_at = now
        fields = ["next_check_at", "updated_at"]
        if collection is not None and payout is None:
            # Extends a pending checkout's window and revives an expired one.
            row.provider_state = {**row.provider_state, "webhook_at": stamp(now)}
            fields.append("provider_state")
        row.save(update_fields=fields)
