"""Persist preferences without claiming an unconfigured delivery service can send."""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.access_state import require_verified_access
from apps.audit.runtime_settings import runtime_settings
from apps.audit.services import record_event
from apps.common.permissions import CanManageOrganization, IsPlatformSuperuser
from apps.common.workspaces import resolve_workspace
from apps.organizations.models import Organization

from .messaging import channel_readiness
from .models import MessagingSettings, NotificationPreferences, ReminderPreferences
from .phone_messaging import personal_phone_preferences, save_user_consent


class SettingsWriteThrottle(UserRateThrottle):
    scope = "settings_write"
    rate = "60/hour"


class StrictSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({key: "Unknown setting." for key in unknown})
        return super().to_internal_value(data)


class PersonalSerializer(StrictSerializer):
    def to_representation(self, instance):
        return personal_phone_preferences(instance.user, super().to_representation(instance))

    class Meta:
        model = NotificationPreferences
        exclude = ["id", "user"]


class ReminderSerializer(StrictSerializer):
    class Meta:
        model = ReminderPreferences
        exclude = ["id", "organization", "run_date", "run_after_id", "next_run_at"]
        extra_kwargs = {
            "before_due_days": {"min_value": 0, "max_value": 30},
            "due_hour": {"min_value": 0, "max_value": 23},
            "overdue_every_days": {"min_value": 1, "max_value": 30},
            "overdue_repeats": {"min_value": 0, "max_value": 3},
        }

    def update(self, instance, validated_data):
        # The scheduler works out the next run from the new schedule.
        instance.next_run_at = None
        return super().update(instance, validated_data)


class MessagingSerializer(StrictSerializer):
    class Meta:
        model = MessagingSettings
        exclude = ["id"]

    def validate(self, attrs):
        start = attrs.get("quiet_from", self.instance.quiet_from)
        end = attrs.get("quiet_until", self.instance.quiet_until)
        if start == end:
            raise serializers.ValidationError({"quiet_until": "Choose a different ending time."})
        return attrs


class WorkspaceSerializer(StrictSerializer):
    class Meta:
        model = Organization
        fields = [
            "display_name",
            "email",
            "phone_number",
            "address",
            "town",
            "country",
            "currency",
            "timezone",
        ]
        read_only_fields = ["currency"]
        extra_kwargs = {"address": {"max_length": 2000}}

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError):
            raise serializers.ValidationError("Choose a valid time zone.") from None
        return value

    def update(self, instance, validated_data):
        if validated_data.get("timezone", instance.timezone) != instance.timezone:
            ReminderPreferences.objects.filter(organization=instance).update(next_run_at=None)
        return super().update(instance, validated_data)

    def validate_phone_number(self, value):
        import re

        if value and not re.fullmatch(r"\+?[0-9 ()-]{7,40}", value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value


class PreferenceView(APIView):
    permission_classes = [IsAuthenticated]
    model = NotificationPreferences
    serializer_class = PersonalSerializer
    create_missing = True

    def get_row(self, lookup):
        if not self.create_missing:
            return get_object_or_404(self.model, **lookup)
        return self.model.objects.get_or_create(**lookup)[0]

    def read_row(self, lookup):
        # Reading never writes: show defaults until the first save.
        if not self.create_missing:
            return get_object_or_404(self.model, **lookup)
        return self.model.objects.filter(**lookup).first() or self.model(**lookup)

    def get_throttles(self):
        return (
            [SettingsWriteThrottle()] if self.request.method == "PATCH" else super().get_throttles()
        )

    def lookup(self, request):
        require_verified_access(request.user, request)
        return {"user": request.user}

    def payload(self, value):
        return {"preferences": self.serializer_class(value).data, "channels": channel_readiness()}

    def get(self, request):
        value = self.read_row(self.lookup(request))
        return Response(self.payload(value))

    def patch(self, request):
        lookup = self.lookup(request)
        with transaction.atomic():
            value = self.get_row(lookup)
            value = self.model.objects.select_for_update().get(pk=value.pk)
            serializer = self.serializer_class(value, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if self.model is NotificationPreferences:
                save_user_consent(request.user, serializer.validated_data)
            record_event(
                request,
                "settings.preferences_updated",
                value,
                organization=lookup.get("organization"),
                fields=list(serializer.validated_data),
                **({"consent_policy_version": "2026-10-26", "consent": {
                    channel: serializer.validated_data[f"{channel}_enabled"]
                    for channel in ("sms", "whatsapp")
                    if f"{channel}_enabled" in serializer.validated_data
                }} if self.model is NotificationPreferences else {}),
            )
        return Response(self.payload(value))

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class ReminderSettingsView(PreferenceView):
    permission_classes = [CanManageOrganization]
    model = ReminderPreferences
    serializer_class = ReminderSerializer

    def lookup(self, request):
        return {"organization": resolve_workspace(request)}


class PlatformMessagingView(PreferenceView):
    permission_classes = [IsPlatformSuperuser]
    model = MessagingSettings
    serializer_class = MessagingSerializer

    def lookup(self, request):
        return {"pk": 1}

    def payload(self, value):
        config = runtime_settings()
        return {
            **super().payload(value),
            "providers": {
                "email": {
                    "routing_enabled": settings.EMAIL_ROUTING_ENABLED,
                    "google_limit": config["email_daily_limit"],
                    "resend_configured": bool(
                        settings.RESEND_API_KEY and settings.RESEND_FROM_EMAIL
                    ),
                    "resend_daily_limit": settings.RESEND_DAILY_LIMIT,
                    "resend_monthly_limit": settings.RESEND_MONTHLY_LIMIT,
                },
                "sms": {"sandbox": settings.AFRICASTALKING_SANDBOX},
                "whatsapp": {"rent_template_configured": bool(config["whatsapp_template"])},
            },
        }


class WorkspaceSettingsView(PreferenceView):
    permission_classes = [CanManageOrganization]
    model = Organization
    serializer_class = WorkspaceSerializer
    create_missing = False

    def lookup(self, request):
        return {"pk": resolve_workspace(request).pk}

    def payload(self, value):
        return self.serializer_class(value).data
