"""Prove exact-number control before enabling operational phone notifications."""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.access_state import require_verified_access
from apps.audit.services import record_event
from apps.common.workspaces import resolve_workspace

from .models import NotificationPhoneLink, NotificationPreferences, PhoneMessagingConsent
from .phone_messaging import normalize_phone


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def receive_link(channel, phone, text, stamp):
    """Called only after provider signature/token + business-number checks."""
    parts = text.strip().split()
    if len(parts) != 2 or parts[0].casefold() != "connect" or len(parts[1]) > 100:
        return False
    now = timezone.now()
    return bool(
        NotificationPhoneLink.objects.filter(
            channel=channel,
            phone=phone,
            token_hash=digest(parts[1]),
            consumed_at__isnull=True,
            verified_at__isnull=True,
            expires_at__gt=now,
            # Meta timestamps have whole-second precision.
            created_at__lt=stamp + timedelta(seconds=1),
            user__is_active=True,
        ).update(verified_at=now)
    )


class LinkThrottle(UserRateThrottle):
    scope = "notification_phone_link"
    rate = "5/hour"


class LinkSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=["sms", "whatsapp"])
    phone = serializers.CharField(max_length=32, required=False)
    consent = serializers.BooleanField(required=False, default=False)
    complete = serializers.IntegerField(min_value=1, required=False)

    def validate(self, attrs):
        if "complete" not in attrs:
            phone = normalize_phone(attrs.get("phone"))
            if not phone or not attrs["consent"]:
                raise ValidationError("Enter a valid number and agree to optional notifications.")
            attrs["phone"] = phone
        return attrs


class PhoneLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        return [LinkThrottle()] if self.request.method == "POST" else []

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        require_verified_access(request.user, request)
        resolve_workspace(request)
        if request.user.is_staff or request.user.is_superuser:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Use a tenant or property manager account.")

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response

    def get(self, request):
        now = timezone.now()
        return Response(
            {
                "links": list(
                    PhoneMessagingConsent.objects.filter(
                        user=request.user,
                        source="verified_link",
                    ).values("channel", "phone", "allowed")
                ),
                "pending": list(
                    NotificationPhoneLink.objects.filter(
                        user=request.user,
                        consumed_at__isnull=True,
                        expires_at__gt=now,
                    )
                    .order_by("-pk")
                    .values("id", "channel", "phone", "verified_at")[:5]
                ),
            }
        )

    @transaction.atomic
    def post(self, request):
        serializer = LinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        channel, now = data["channel"], timezone.now()
        if "complete" in data:
            link = (
                NotificationPhoneLink.objects.select_for_update()
                .filter(
                    pk=data["complete"],
                    user=request.user,
                    channel=channel,
                    consumed_at__isnull=True,
                    verified_at__isnull=False,
                    expires_at__gt=now,
                )
                .first()
            )
            if not link:
                raise ValidationError("Verify your number before completing this connection.")
            consent, _ = PhoneMessagingConsent.objects.get_or_create(
                channel=channel,
                phone=link.phone,
                defaults={"source": "verified_link"},
            )
            consent = PhoneMessagingConsent.objects.select_for_update().get(pk=consent.pk)
            if consent.user_id not in {None, request.user.pk} and consent.allowed:
                raise ValidationError("This number cannot be connected. Contact support.")
            # One current verified notification number per user/channel.
            PhoneMessagingConsent.objects.filter(user=request.user, channel=channel).exclude(
                pk=consent.pk,
            ).update(allowed=False, revoked_at=now)
            consent.user, consent.allowed, consent.source = request.user, True, "verified_link"
            consent.granted_at, consent.last_inbound_at = now, link.verified_at
            consent.save()
            link.consumed_at = now
            link.save(update_fields=["consumed_at"])
            pref, _ = NotificationPreferences.objects.get_or_create(user=request.user)
            setattr(pref, f"{channel}_enabled", True)
            pref.save(update_fields=[f"{channel}_enabled"])
            record_event(request, "notifications.phone_connected", pref, channel=channel)
            return Response({"connected": True, "channel": channel, "phone": link.phone})
        configured_destination = (
            settings.WHATSAPP_PUBLIC_NUMBER
            if channel == "whatsapp" else settings.SMS_INCOMING_NUMBER
        ).strip()
        destination = normalize_phone(configured_destination)
        if channel == "sms" and configured_destination.isascii() and (
            configured_destination.isdecimal() and 3 <= len(configured_destination) <= 6
        ):
            destination = configured_destination
        if not destination:
            raise ValidationError("This channel is not connected yet. Email remains available.")
        NotificationPhoneLink.objects.filter(
            user=request.user,
            channel=channel,
            consumed_at__isnull=True,
        ).update(consumed_at=now)
        token = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(8))
        link = NotificationPhoneLink.objects.create(
            user=request.user,
            channel=channel,
            phone=data["phone"],
            token_hash=digest(token),
            expires_at=now + timedelta(minutes=10),
        )
        record_event(request, "notifications.phone_link_requested", channel=channel)
        return Response(
            {
                "id": link.pk,
                "destination": destination,
                "message": f"CONNECT {token}",
                "expires_at": link.expires_at,
            }
        )
