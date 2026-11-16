"""Requested WhatsApp codes. Secrets stay out of API responses, logs and storage."""

import hmac
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework import serializers
from rest_framework.exceptions import APIException, Throttled, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle

from apps.audit.provider_credentials import credential
from apps.audit.runtime_settings import approved_whatsapp_templates
from apps.audit.services import record_event
from apps.common.provider_http import ProviderRejected, post_json

from .models import NotificationPhoneLink
from .phone_links import LinkIPThrottle, LinkThrottle, PhoneLinkView, complete_link, digest
from .phone_messaging import normalize_phone, phone_allowed, whatsapp_ready
from .whatsapp.access import auth_stamp, require_actor

INVALID = "This code is invalid or expired. Request a new code."


class Unavailable(APIException):
    status_code = 503
    default_detail = "WhatsApp verification is unavailable. Please try again later."


def ready():
    return bool(
        settings.WHATSAPP_OTP_ENABLED
        and settings.WHATSAPP_SELF_SERVICE_ENABLED
        and whatsapp_ready()
        and f"{settings.WHATSAPP_OTP_TEMPLATE}:{settings.WHATSAPP_OTP_LANGUAGE}"
        in approved_whatsapp_templates()
    )


def code_hash(link, code):
    value = f"{link.user_id}:{link.phone}:{link.verification_nonce}:{link.auth_stamp}:{code}"
    return salted_hmac("dwella.whatsapp.phone-code", value, algorithm="sha256").hexdigest()


class CodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32, required=False)
    consent = serializers.BooleanField(default=False)
    complete = serializers.IntegerField(min_value=1, required=False)
    code = serializers.RegexField(r"^[0-9]{6}$", required=False, max_length=6)

    def validate(self, attrs):
        if "complete" in attrs:
            if "code" not in attrs:
                raise ValidationError({"code": "Enter the six-digit code from WhatsApp."})
        else:
            attrs["phone"] = normalize_phone(attrs.get("phone"))
            if not attrs["phone"]:
                raise ValidationError({"phone": "Enter a valid international phone number."})
        return attrs


class CodeAttemptThrottle(UserRateThrottle):
    scope = "whatsapp_code_attempt"
    rate = "30/hour"


class CodeNumberThrottle(SimpleRateThrottle):
    scope = "whatsapp_link_number"
    rate = "10/hour"

    def get_cache_key(self, request, view):
        phone = normalize_phone(request.data.get("phone")) if isinstance(request.data, dict) else ""
        return self.cache_format % {"scope": self.scope, "ident": digest(phone)} if phone else None


class PhoneCodeView(PhoneLinkView):
    http_method_names = ["post", "options"]

    def get_throttles(self):
        if isinstance(self.request.data, dict) and self.request.data.get("complete"):
            return [CodeAttemptThrottle(), LinkIPThrottle()]
        return [LinkThrottle(), CodeNumberThrottle(), LinkIPThrottle()]

    def post(self, request):
        require_actor(request.user)
        serializer = CodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "complete" in data:
            return self.confirm(request, data)
        if not ready() or not phone_allowed(data["phone"]):
            raise Unavailable()
        now = timezone.now()
        code = f"{secrets.randbelow(1_000_000):06d}"
        # Serialise requests for this account; no provider I/O within the lock.
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
            require_actor(user)
            if NotificationPhoneLink.objects.filter(
                user=user,
                channel="whatsapp",
                verification_nonce__isnull=False,
                created_at__gt=now - timedelta(seconds=60),
            ).exists():
                raise Throttled(wait=60, detail="Wait a minute before requesting another code.")
            NotificationPhoneLink.objects.filter(
                user=user,
                channel="whatsapp",
                consumed_at__isnull=True,
            ).update(consumed_at=now)
            link = NotificationPhoneLink(
                user=user,
                channel="whatsapp",
                phone=data["phone"],
                verification_nonce=uuid.uuid4(),
                auth_stamp=auth_stamp(user),
                expires_at=now + timedelta(minutes=10),
                actions_enabled=True,
                notification_consent=data["consent"],
                delivery_status="sending",
            )
            link.token_hash = code_hash(link, code)
            link.save()
            record_event(request, "notifications.phone_code_requested", channel="whatsapp")
        payload = {
            "messaging_product": "whatsapp",
            "to": link.phone[1:],
            "type": "template",
            "template": {
                "name": settings.WHATSAPP_OTP_TEMPLATE,
                "language": {"code": settings.WHATSAPP_OTP_LANGUAGE},
                "components": [
                    {"type": "body", "parameters": [{"type": "text", "text": code}]},
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [{"type": "text", "text": code}],
                    },
                ],
            },
        }
        status, provider_id = "review", ""
        try:
            # No retries: an uncertain response may already have delivered the code.
            result = post_json(
                f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/"
                f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
                payload,
                {"Authorization": f"Bearer {credential('WHATSAPP_ACCESS_TOKEN')}"},
            )
            provider_id = result["messages"][0]["id"]
            if not isinstance(provider_id, str) or not 1 <= len(provider_id) <= 160:
                provider_id = ""
                raise ValueError("Invalid provider identity.")
            status = "sent"
        except ProviderRejected as error:
            status = "review" if error.code.startswith("http_5") else "failed"
        except Exception:
            pass
        NotificationPhoneLink.objects.filter(pk=link.pk).update(
            delivery_status=status,
            provider_id=provider_id,
        )
        if status == "failed":
            raise Unavailable()
        return Response(
            {
                "id": link.pk,
                "phone": link.phone,
                "expires_at": link.expires_at,
                "retry_after": 60,
                "delivery_status": status,
            },
            status=202,
        )

    def confirm(self, request, data):
        result = None
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
            require_actor(user)
            link = (
                NotificationPhoneLink.objects.select_for_update()
                .filter(
                    pk=data["complete"],
                    user=user,
                    channel="whatsapp",
                    verification_nonce__isnull=False,
                    consumed_at__isnull=True,
                    expires_at__gt=timezone.now(),
                    failed_attempts__lt=5,
                    delivery_status__in=["sending", "sent", "review"],
                )
                .first()
            )
            if link and link.auth_stamp == auth_stamp(user):
                if hmac.compare_digest(link.token_hash, code_hash(link, data["code"])):
                    link.verified_at = timezone.now()
                    link.save(update_fields=["verified_at"])
                    result = complete_link(request, link, link.verified_at)
                else:
                    link.failed_attempts += 1
                    link.save(update_fields=["failed_attempts"])
        # Raise after commit so invalid attempts cannot roll back their counter.
        if result is None:
            raise ValidationError({"code": INVALID})
        return Response(result)
