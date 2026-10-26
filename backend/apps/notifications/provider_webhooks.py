"""Signed Meta callbacks. Store delivery evidence, never an inbound chat history."""

import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .models import MessageDelivery, PhoneMessagingConsent
from .phone_messaging import normalize_phone, phone_variants

MAX_BODY = 256 * 1024
STOP_WORDS = {"stop", "unsubscribe", "cancel", "stop all", "opt out"}


class CallbackThrottle(AnonRateThrottle):
    scope = "messaging_callback"
    rate = "600/min"


def event_time(value):
    try:
        result = datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OverflowError, OSError):
        raise ValueError("Invalid event timestamp.") from None
    if result > timezone.now() + timedelta(minutes=5):
        raise ValueError("Future event timestamp.")
    return result


@transaction.atomic
def apply_status(data):
    provider_id, status = data.get("id"), data.get("status")
    if not isinstance(provider_id, str) or len(provider_id) > 160:
        raise ValueError("Invalid provider ID.")
    if status not in {"sent", "delivered", "read", "failed"}:
        return
    stamp = event_time(data.get("timestamp"))
    query = Q(provider="whatsapp", provider_id=provider_id)
    reference = data.get("biz_opaque_callback_data")
    if reference:
        # An authentic callback may arrive before the send response is persisted.
        import uuid

        try:
            reference = uuid.UUID(reference)
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Invalid callback reference.") from None
        query |= Q(public_id=reference, channel="whatsapp", status="sending", provider_id="")
    row = MessageDelivery.objects.select_for_update().filter(query, channel="whatsapp").first()
    if not row:
        return
    if normalize_phone("+" + str(data.get("recipient_id", ""))) != normalize_phone(row.recipient):
        return
    ranks = {"sending": 0, "review": 0, "sent": 1, "failed": 2, "delivered": 3, "read": 4}
    # Repeated and out-of-order events do not regress confirmed delivery/read evidence.
    if ranks.get(status, -1) < ranks.get(row.status, 99):
        return
    if row.provider_updated_at and stamp < row.provider_updated_at:
        return
    updates = {
        "status": status,
        "provider": "whatsapp",
        "provider_id": provider_id,
        "provider_updated_at": stamp,
        "reason": "provider_" + status,
    }
    if status in {"delivered", "read"}:
        updates["delivered_at"] = row.delivered_at or stamp
    if status == "read":
        updates["read_at"] = row.read_at or stamp
    if status == "failed":
        errors = data.get("errors", [])
        if not isinstance(errors, list) or (errors and not isinstance(errors[0], dict)):
            raise ValueError("Invalid failure details.")
        updates["failure_code"] = (
            str(errors[0].get("code", "unknown"))[:80] if errors else "unknown"
        )
    else:
        updates["failure_code"] = ""
    MessageDelivery.objects.filter(pk=row.pk).update(**updates)


@transaction.atomic
def apply_inbound(message):
    phone = normalize_phone("+" + str(message.get("from", "")))
    if not phone:
        raise ValueError("Invalid sender.")
    stamp = event_time(message.get("timestamp"))
    # Stale replays must never reopen a customer-service window.
    if stamp < timezone.now() - timedelta(days=7):
        return
    text = message.get("text", {}).get("body", "") if message.get("type") == "text" else ""
    if not isinstance(text, str):
        raise ValueError("Invalid message.")
    button = message.get("button", {}) if message.get("type") == "button" else {}
    stop = (
        text.strip().casefold() in STOP_WORDS or button.get("payload", "").casefold() in STOP_WORDS
    )
    consent, _ = PhoneMessagingConsent.objects.get_or_create(
        channel="whatsapp",
        phone=phone,
        defaults={"source": "whatsapp_inbound"},
    )
    consent = PhoneMessagingConsent.objects.select_for_update().get(pk=consent.pk)
    consent.last_inbound_at = max(consent.last_inbound_at or stamp, stamp)
    revoked = stop and (
        not consent.granted_at or stamp >= consent.granted_at.replace(microsecond=0)
    )
    if revoked:
        consent.allowed, consent.revoked_at, consent.source = False, stamp, "whatsapp_stop"
    # A greeting or START alone does not grant ongoing reminder consent.
    consent.save()
    if revoked:
        # Queued jobs are cancelled promptly; dispatch also rechecks consent.
        MessageDelivery.objects.filter(
            channel="whatsapp",
            recipient__in=phone_variants(phone),
            status__in=["held", "queued"],
        ).update(status="cancelled", reason="recipient_opted_out")


class WhatsAppWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CallbackThrottle]

    def get(self, request):
        token = settings.WHATSAPP_VERIFY_TOKEN
        supplied = request.query_params.get("hub.verify_token", "")
        if (
            not token
            or request.query_params.get("hub.mode") != "subscribe"
            or not hmac.compare_digest(token.encode(), supplied.encode())
        ):
            return Response({"detail": "Verification failed."}, status=403)
        challenge = request.query_params.get("hub.challenge", "")
        if not challenge.isdecimal() or len(challenge) > 100:
            return Response({"detail": "Invalid challenge."}, status=400)
        return HttpResponse(challenge, content_type="text/plain")

    def post(self, request):
        try:
            size = int(request.META.get("CONTENT_LENGTH") or 0)
        except (ValueError, TypeError):
            return Response({"detail": "Invalid content length."}, status=400)
        if size > MAX_BODY:
            return Response({"detail": "Callback too large."}, status=413)
        raw = request.body
        if len(raw) > MAX_BODY:
            return Response({"detail": "Callback too large."}, status=413)
        secret = settings.WHATSAPP_APP_SECRET
        expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        if not secret or not hmac.compare_digest(
            expected.encode(), request.headers.get("X-Hub-Signature-256", "").encode()
        ):
            return Response({"detail": "Invalid signature."}, status=403)
        try:
            payload = json.loads(raw)
            if payload.get("object") != "whatsapp_business_account":
                raise ValueError("Invalid object.")
            entries = payload.get("entry", [])
            if not isinstance(entries, list) or len(entries) > 100:
                raise ValueError("Invalid entries.")
            with transaction.atomic():
                for entry in entries:
                    if str(entry.get("id")) != settings.WHATSAPP_BUSINESS_ACCOUNT_ID:
                        continue
                    changes = entry.get("changes", [])
                    if not isinstance(changes, list) or len(changes) > 100:
                        raise ValueError("Invalid changes.")
                    for change in changes:
                        if change.get("field") != "messages":
                            continue
                        value = change["value"]
                        if str(value.get("metadata", {}).get("phone_number_id")) != (
                            settings.WHATSAPP_PHONE_NUMBER_ID
                        ):
                            continue
                        statuses, messages = value.get("statuses", []), value.get("messages", [])
                        if not isinstance(statuses, list) or not isinstance(messages, list):
                            raise ValueError("Invalid events.")
                        if len(statuses) + len(messages) > 100:
                            raise ValueError("Too many events.")
                        for status in statuses:
                            apply_status(status)
                        for message in messages:
                            apply_inbound(message)
        except (ValueError, TypeError, KeyError, AttributeError):
            return Response({"detail": "Invalid callback."}, status=400)
        return Response({"received": True})


class SMSWebhookView(APIView):
    """AT callbacks use a high-entropy callback URL token over HTTPS.

    This is a bearer credential, not a provider body signature. Proxy and Gunicorn
    access logging omit query strings so the token is not written to access logs.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [CallbackThrottle]
    kind = "delivery"

    def post(self, request):
        token = settings.AFRICASTALKING_CALLBACK_TOKEN
        if len(token) < 32 or not hmac.compare_digest(
            token.encode(),
            request.query_params.get("token", "").encode(),
        ):
            return Response({"detail": "Invalid callback credentials."}, status=403)
        if len(request.body) > MAX_BODY:
            return Response({"detail": "Callback too large."}, status=413)
        data = request.data
        if not isinstance(data, dict):
            return Response({"detail": "Invalid callback."}, status=400)
        if self.kind in {"opt-out", "incoming"}:
            return self.opt_out(data)
        provider_id, status = data.get("id"), data.get("status")
        if not isinstance(provider_id, str) or not provider_id or len(provider_id) > 160:
            return Response({"detail": "Invalid message ID."}, status=400)
        statuses = {
            "Success": "delivered",
            "Failed": "failed",
            "Rejected": "failed",
            "Submitted": "sent",
            "Buffered": "sent",
            "Sent": "sent",
        }
        if status not in statuses:
            return Response({"detail": "Invalid status."}, status=400)
        with transaction.atomic():
            row = (
                MessageDelivery.objects.select_for_update()
                .filter(
                    provider="africastalking",
                    provider_id=provider_id,
                    channel="sms",
                )
                .first()
            )
            if not row:
                # AT can report delivery before the HTTP send response reaches us.
                # Ask it to retry while a sending claim is still awaiting its ID.
                sending = MessageDelivery.objects.filter(
                    channel="sms",
                    status="sending",
                    claimed_at__gte=timezone.now() - timedelta(minutes=10),
                ).exists()
                return Response({"received": not sending}, status=503 if sending else 200)
            supplied_phone = data.get("phoneNumber")
            if supplied_phone and normalize_phone(supplied_phone) != normalize_phone(row.recipient):
                return Response({"detail": "Recipient mismatch."}, status=400)
            target = statuses[status]
            ranks = {"sending": 0, "review": 0, "sent": 1, "failed": 2, "delivered": 3}
            if ranks[target] >= ranks.get(row.status, 99):
                fields = {
                    "status": target,
                    "provider_updated_at": timezone.now(),
                    "reason": "provider_" + target,
                }
                if target == "delivered":
                    fields["delivered_at"] = row.delivered_at or timezone.now()
                    fields["failure_code"] = ""
                elif target == "failed":
                    fields["failure_code"] = "at_" + status.lower()
                MessageDelivery.objects.filter(pk=row.pk).update(**fields)
        return Response({"received": True})

    def opt_out(self, data):
        phone = normalize_phone(
            data.get("phoneNumber") if self.kind == "opt-out" else (data.get("from"))
        )
        sender = data.get("senderId") if self.kind == "opt-out" else data.get("to")
        if not phone or sender != settings.AFRICASTALKING_SENDER_ID:
            return Response({"detail": "Invalid opt-out."}, status=400)
        if self.kind == "incoming":
            text = data.get("text", "")
            if not isinstance(text, str):
                return Response({"detail": "Invalid message."}, status=400)
            if text.strip().casefold() not in STOP_WORDS:
                return Response({"received": True})
        with transaction.atomic():
            PhoneMessagingConsent.objects.update_or_create(
                channel="sms",
                phone=phone,
                defaults={"allowed": False, "source": "sms_opt_out", "revoked_at": timezone.now()},
            )
            MessageDelivery.objects.filter(
                channel="sms",
                recipient__in=phone_variants(phone),
                status__in=["held", "queued"],
            ).update(status="cancelled", reason="recipient_opted_out")
        return Response({"received": True})
