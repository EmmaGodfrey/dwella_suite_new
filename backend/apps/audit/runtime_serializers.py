import re

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.common.mail import delivery_configured

from .runtime_settings import (
    approved_senders,
    approved_sms_senders,
    approved_whatsapp_templates,
    assistant_configured,
    runtime_settings,
    safe_assistant_url,
)


class RuntimeSettingsSerializer(serializers.Serializer):
    assistant_url = serializers.URLField(max_length=500, allow_blank=True, required=False)
    assistant_title = serializers.CharField(max_length=80, required=False)
    assistant_suggestions = serializers.ListField(
        child=serializers.CharField(max_length=160), max_length=6, required=False
    )
    support_email = serializers.EmailField(allow_blank=True, required=False)
    support_phone = serializers.CharField(max_length=40, allow_blank=True, required=False)
    support_whatsapp = serializers.RegexField(
        r"^\+?[1-9]\d{7,14}$", allow_blank=True, required=False
    )
    support_help_url = serializers.URLField(max_length=500, allow_blank=True, required=False)
    email_sender_name = serializers.CharField(max_length=100, allow_blank=True, required=False)
    email_from_address = serializers.EmailField(required=False)
    email_reply_to = serializers.EmailField(allow_blank=True, required=False)
    email_daily_limit = serializers.IntegerField(min_value=1, max_value=400, required=False)
    messaging_email_enabled = serializers.BooleanField(required=False)
    sms_enabled = serializers.BooleanField(required=False)
    sms_sender_id = serializers.RegexField(
        r"^[A-Za-z0-9 ._-]{1,20}$", allow_blank=True, required=False
    )
    whatsapp_enabled = serializers.BooleanField(required=False)
    whatsapp_template = serializers.RegexField(
        r"^[a-z0-9_]{1,120}$", allow_blank=True, required=False
    )
    whatsapp_language = serializers.RegexField(r"^[a-z]{2,3}(?:_[A-Z]{2})?$", required=False)
    beta_registration_open = serializers.BooleanField(required=False)
    beta_emails_enabled = serializers.BooleanField(required=False)
    beta_open_date = serializers.DateField(required=False)
    launch_date = serializers.DateField(required=False)
    beta_countdown_days = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=60),
        min_length=3,
        max_length=3,
        required=False,
    )
    beta_send_hour = serializers.IntegerField(min_value=0, max_value=23, required=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Expected an object of settings.")
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: "Unknown setting." for key in unknown})
        return super().to_internal_value(data)

    def validate_assistant_url(self, value):
        value = value.rstrip("/")
        if value and not safe_assistant_url(value):
            raise serializers.ValidationError("Choose an approved HTTPS Handy address.")
        return value

    def validate_support_help_url(self, value):
        if value and not value.startswith("https://"):
            raise serializers.ValidationError("Use an HTTPS help link.")
        return value

    def validate_support_phone(self, value):
        if value and (
            not re.fullmatch(r"\+?[0-9 ()-]{8,40}", value)
            or not 7 <= len(re.sub(r"\D", "", value)) <= 15
        ):
            raise serializers.ValidationError("Enter a valid support phone number.")
        return value

    def validate_email_from_address(self, value):
        value = value.lower()
        if value not in approved_senders():
            raise serializers.ValidationError("Choose a sender approved for this environment.")
        return value

    def validate_email_sender_name(self, value):
        if re.search(r"[\r\n]", value):
            raise serializers.ValidationError("Use a single-line sender name.")
        return value

    def validate_email_daily_limit(self, value):
        if value > settings.EMAIL_GOOGLE_LIMIT:
            raise serializers.ValidationError("Exceeds this environment's sending allowance.")
        return value

    def validate_beta_countdown_days(self, value):
        if sorted(set(value), reverse=True) != value:
            raise serializers.ValidationError("Use three different day offsets, largest first.")
        return value

    def validate(self, attrs):
        existing = runtime_settings(instance=self.instance)
        for key in ("beta_open_date", "launch_date"):
            if key in attrs:
                attrs[key] = attrs[key].isoformat()
        effective = {**existing, **attrs}
        if effective["launch_date"] < effective["beta_open_date"]:
            raise serializers.ValidationError(
                {"launch_date": "Launch must follow the beta opening."}
            )
        failures = {}
        if (
            "messaging_email_enabled" in attrs
            and effective["messaging_email_enabled"]
            and not delivery_configured()
        ):
            failures["messaging_email_enabled"] = "Configure an email connection first."
        if (
            "beta_emails_enabled" in attrs
            and effective["beta_emails_enabled"]
            and not delivery_configured()
        ):
            failures["beta_emails_enabled"] = "Configure an email connection first."
        if effective["sms_enabled"] and set(attrs) & {"sms_enabled", "sms_sender_id"}:
            if not all(
                (
                    settings.AFRICASTALKING_USERNAME,
                    settings.AFRICASTALKING_API_KEY,
                    effective["sms_sender_id"],
                    len(settings.AFRICASTALKING_CALLBACK_TOKEN) >= 32,
                )
            ):
                failures["sms_enabled"] = "Complete Africa's Talking credentials and sender setup."
            elif effective["sms_sender_id"] not in approved_sms_senders():
                failures["sms_sender_id"] = "Choose an approved SMS sender."
        if effective["whatsapp_enabled"] and set(attrs) & {
            "whatsapp_enabled",
            "whatsapp_template",
            "whatsapp_language",
        }:
            if not all(
                (
                    settings.WHATSAPP_ACCESS_TOKEN,
                    settings.WHATSAPP_PHONE_NUMBER_ID,
                    settings.WHATSAPP_BUSINESS_ACCOUNT_ID,
                    settings.WHATSAPP_APP_SECRET,
                    settings.WHATSAPP_VERIFY_TOKEN,
                    effective["whatsapp_template"],
                )
            ):
                failures["whatsapp_enabled"] = "Complete Meta credentials and template setup."
            elif (
                f"{effective['whatsapp_template']}:{effective['whatsapp_language']}"
                not in approved_whatsapp_templates()
            ):
                failures["whatsapp_template"] = "Choose an approved template and language."
        if failures:
            raise serializers.ValidationError(failures)
        return attrs

    def update(self, instance, validated_data):
        old = runtime_settings(instance=instance)
        values = {**instance.runtime_config, **validated_data}
        if values.get("assistant_url", old["assistant_url"]) != old["assistant_url"]:
            values.pop("assistant_verified_url", None)
            instance.handy_agent_enabled = False
        if (
            (validated_data.get("beta_emails_enabled") and not old["beta_emails_enabled"])
            or validated_data.get("beta_open_date", old["beta_open_date"]) != old["beta_open_date"]
            or validated_data.get("beta_countdown_days", old["beta_countdown_days"])
            != old["beta_countdown_days"]
            or validated_data.get("beta_send_hour", old["beta_send_hour"]) != old["beta_send_hour"]
        ):
            values["beta_schedule_changed_at"] = timezone.now().isoformat()
        instance.runtime_config = values
        instance.save(update_fields=["runtime_config", "handy_agent_enabled"])
        return instance

    def to_representation(self, instance):
        config = runtime_settings(instance=instance)
        return {key: config[key] for key in self.fields}


def readiness(instance):
    config = runtime_settings(instance=instance)
    return {
        "assistant_configured": assistant_configured(config),
        "assistant_verified": bool(config.get("assistant_verified_url")),
        "approved_email_senders": approved_senders(),
        "approved_sms_senders": approved_sms_senders(),
        "approved_whatsapp_templates": approved_whatsapp_templates(),
        "email_configured": delivery_configured(),
        "email_daily_max": min(400, settings.EMAIL_GOOGLE_LIMIT),
        "sms_credentials_configured": bool(
            settings.AFRICASTALKING_USERNAME
            and settings.AFRICASTALKING_API_KEY
            and len(settings.AFRICASTALKING_CALLBACK_TOKEN) >= 32
        ),
        "whatsapp_credentials_configured": bool(
            settings.WHATSAPP_ACCESS_TOKEN
            and settings.WHATSAPP_PHONE_NUMBER_ID
            and settings.WHATSAPP_BUSINESS_ACCOUNT_ID
            and settings.WHATSAPP_APP_SECRET
            and settings.WHATSAPP_VERIFY_TOKEN
        ),
    }
