"""Prove exact-number control before enabling operational phone notifications."""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle
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
    verified = bool(
        NotificationPhoneLink.objects.filter(
            channel=channel,
            phone=phone,
            token_hash=digest(parts[1]),
            consumed_at__isnull=True,
            verified_at__isnull=True,
            expires_at__gt=now,
            failed_attempts__lt=5,
            # Meta timestamps have whole-second precision.
            created_at__lt=stamp + timedelta(seconds=1),
            user__is_active=True,
        ).update(verified_at=now)
    )
    if not verified:
        NotificationPhoneLink.objects.filter(
            channel=channel, phone=phone, expires_at__gt=now, consumed_at__isnull=True,
            verified_at__isnull=True, failed_attempts__lt=5,
        ).update(failed_attempts=F('failed_attempts') + 1)
    return verified


class LinkThrottle(UserRateThrottle):
    scope = "notification_phone_link"
    rate = "5/hour"


class LinkNumberThrottle(SimpleRateThrottle):
    scope = "whatsapp_link_number"
    rate = "10/hour"

    def get_cache_key(self, request, view):
        if not isinstance(request.data, dict):
            return None
        if request.data.get("complete") or request.data.get("channel") != "whatsapp":
            return None
        phone = normalize_phone(request.data.get("phone"))
        return self.cache_format % {"scope": self.scope, "ident": digest(phone)} if phone else None


class LinkIPThrottle(SimpleRateThrottle):
    scope = "notification_link_ip"
    rate = "30/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class DisconnectThrottle(UserRateThrottle):
    scope = "whatsapp_disconnect"
    rate = "30/hour"


class LinkSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=["sms", "whatsapp"])
    phone = serializers.CharField(max_length=32, required=False)
    consent = serializers.BooleanField(required=False, default=False)
    complete = serializers.IntegerField(min_value=1, required=False)
    actions = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        if "complete" not in attrs:
            phone = normalize_phone(attrs.get("phone"))
            if not phone:
                raise ValidationError({"phone": "Enter a valid international phone number."})
            if not (attrs["consent"] or (
                attrs["channel"] == "whatsapp" and attrs["actions"]
            )):
                raise ValidationError("Enter a valid number and agree to optional notifications.")
            attrs["phone"] = phone
        return attrs


class PhoneLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        if self.request.method == "POST":
            return [LinkThrottle(), LinkNumberThrottle(), LinkIPThrottle()]
        return [DisconnectThrottle()] if self.request.method == "DELETE" else []

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
                "whatsapp_binding": self.binding_state(request.user),
            }
        )

    @staticmethod
    def binding_state(user):
        from .whatsapp.access import auth_stamp
        from .whatsapp.models import WhatsAppBinding

        binding = WhatsAppBinding.objects.filter(user=user, revoked_at__isnull=True).first()
        if not binding or binding.auth_stamp != auth_stamp(user):
            return None
        return {"phone": binding.phone, "verified_at": binding.verified_at}

    @transaction.atomic
    def delete(self, request):
        from .whatsapp.access import revoke

        revoke(user=request.user)
        now = timezone.now()
        NotificationPhoneLink.objects.filter(
            user=request.user, channel="whatsapp", consumed_at__isnull=True,
        ).update(consumed_at=now)
        PhoneMessagingConsent.objects.filter(user=request.user, channel="whatsapp").update(
            allowed=False, revoked_at=now,
        )
        NotificationPreferences.objects.filter(user=request.user).update(whatsapp_enabled=False)
        record_event(request, "notifications.whatsapp_disconnected")
        return Response({"disconnected": True})

    @transaction.atomic
    def post(self, request):
        serializer = LinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        channel, now = data["channel"], timezone.now()
        if channel == "whatsapp" and data["actions"]:
            from .whatsapp.access import require_actor

            require_actor(request.user)
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
                    failed_attempts__lt=5,
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
            if channel == "whatsapp":
                from .whatsapp.access import bind, revoke

                if link.actions_enabled:
                    bind(request.user, link.phone)
                else:
                    revoke(user=request.user)
            consent.user = request.user
            consent.allowed = link.notification_consent
            consent.source = "verified_link"
            consent.granted_at, consent.last_inbound_at = now, link.verified_at
            consent.revoked_at = None
            consent.save()
            link.consumed_at = now
            link.save(update_fields=["consumed_at"])
            pref, _ = NotificationPreferences.objects.get_or_create(user=request.user)
            setattr(pref, f"{channel}_enabled", link.notification_consent)
            pref.save(update_fields=[f"{channel}_enabled"])
            record_event(request, "notifications.phone_connected", pref, channel=channel)
            return Response({"connected": True, "channel": channel, "phone": link.phone,
                             "actions_connected": link.actions_enabled,
                             "notification_consent": link.notification_consent})
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
            actions_enabled=channel == "whatsapp" and data["actions"],
            notification_consent=data["consent"],
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
