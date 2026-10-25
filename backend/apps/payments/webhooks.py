import hashlib
import hmac
import re

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from .evidence import record_exchange, strict_json
from .models import WebhookReceipt

MAX_WEBHOOK = 128 * 1024
EVENTS = {
    "collection.successful",
    "collection.failed",
    "collection.settled",
    "transfer.successful",
    "transfer.failed",
}


def receive_webhook(body, signature):
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
    digest = hashlib.sha256(body).hexdigest()
    with transaction.atomic():
        # Serialize duplicate deliveries without reversing ledger lock order.
        from .models import Collection, Payout

        if event.startswith("collection."):
            collection = Collection.objects.filter(
                reference=reference, environment=settings.LENCO_ENVIRONMENT
            ).first()
        else:
            payout = Payout.objects.filter(
                reference=reference, collection__environment=settings.LENCO_ENVIRONMENT
            ).first()
            collection = payout.collection if payout else None
        # Other activity in this merchant account is outside Dwella's rent flow.
        if collection is None:
            return
        Collection.objects.select_for_update().get(pk=collection.pk)
        if WebhookReceipt.objects.filter(
            environment=settings.LENCO_ENVIRONMENT, digest=digest
        ).exists():
            return
        exchange = record_exchange(
            environment=settings.LENCO_ENVIRONMENT,
            operation="webhook",
            body=body,
            collection=collection,
        )
        WebhookReceipt.objects.create(
            environment=settings.LENCO_ENVIRONMENT,
            digest=digest,
            reference=reference,
            event=event,
            exchange=exchange,
        )
