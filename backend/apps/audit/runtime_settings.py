"""Typed operational settings. Environment values remain defaults, never secrets in JSON."""

import hashlib
import json
from datetime import date
from email.utils import formataddr, parseaddr
from urllib.parse import urlsplit

from django.conf import settings

from .models import PlatformSettings

SUGGESTIONS = [
    "Which tenants are overdue on rent this month?",
    "How many units are vacant right now?",
    "Which leases end in the next 60 days?",
    "How much rent did I collect last month?",
    "Show open maintenance requests for my properties",
]


def defaults():
    name, address = parseaddr(settings.DEFAULT_FROM_EMAIL)
    return {
        "assistant_url": settings.HANDY_AGENT_URL.rstrip("/"),
        "assistant_title": "Dwella assistant",
        "assistant_suggestions": SUGGESTIONS,
        "support_email": settings.SUPPORT_EMAIL,
        "support_phone": settings.SUPPORT_PHONE,
        "support_whatsapp": "",
        "support_help_url": "",
        "email_sender_name": name,
        "email_from_address": address,
        "email_reply_to": settings.BETA_EMAIL_REPLY_TO,
        "email_daily_limit": settings.EMAIL_GOOGLE_LIMIT,
        "messaging_email_enabled": settings.MESSAGING_EMAIL_ENABLED,
        "sms_enabled": settings.SMS_ENABLED,
        "sms_sender_id": settings.AFRICASTALKING_SENDER_ID,
        "whatsapp_enabled": settings.WHATSAPP_ENABLED,
        "whatsapp_template": settings.WHATSAPP_RENT_TEMPLATE,
        "whatsapp_language": settings.WHATSAPP_TEMPLATE_LANGUAGE,
        "beta_registration_open": settings.BETA_REGISTRATION_OPEN,
        "beta_emails_enabled": settings.BETA_EMAILS_ENABLED,
        "beta_open_date": settings.BETA_OPEN_DATE,
        "launch_date": settings.LAUNCH_DATE,
        "beta_countdown_days": [14, 7, 1],
        "beta_send_hour": 8,
    }


def runtime_settings(*, instance=None, alias="default"):
    # One bounded row read. Callers doing several checks reuse this dictionary.
    saved = (
        instance.runtime_config
        if instance is not None
        else PlatformSettings.objects.using(alias)
        .filter(pk=1)
        .values_list("runtime_config", flat=True)
        .first()
    ) or {}
    return {**defaults(), **saved}


def approved_senders():
    primary = parseaddr(settings.DEFAULT_FROM_EMAIL)[1].lower()
    return sorted({primary, *getattr(settings, "APPROVED_EMAIL_SENDERS", [])} - {""})


def approved_sms_senders():
    return sorted({settings.AFRICASTALKING_SENDER_ID, *settings.APPROVED_SMS_SENDERS} - {""})


def approved_whatsapp_templates():
    base = (
        f"{settings.WHATSAPP_RENT_TEMPLATE}:{settings.WHATSAPP_TEMPLATE_LANGUAGE}"
        if settings.WHATSAPP_RENT_TEMPLATE
        else ""
    )
    return sorted({base, *settings.APPROVED_WHATSAPP_TEMPLATES} - {""})


def assistant_origins():
    return set(settings.HANDY_AGENT_ALLOWED_ORIGINS)


def assistant_verified(config):
    url = config["assistant_url"].rstrip("/")
    # Existing environment-approved connections keep their deployment contract.
    return bool(
        url
        and (
            url == settings.HANDY_AGENT_URL.rstrip("/")
            or config.get("assistant_verified_url") == url
        )
    )


def assistant_configured(config):
    return assistant_verified(config) and len(settings.HANDY_AGENT_SIGNING_SECRET) >= 32


def assistant_payload(*, instance=None):
    instance = instance or PlatformSettings.objects.filter(pk=1).first()
    config = runtime_settings(instance=instance) if instance else defaults()
    enabled = bool(instance and instance.handy_agent_enabled and assistant_configured(config))
    if not enabled:
        return {"enabled": False}
    visible = {
        "url": config["assistant_url"],
        "title": config["assistant_title"],
        "suggestions": config["assistant_suggestions"],
    }
    return {
        "enabled": True,
        **visible,
        "revision": hashlib.sha256(json.dumps(visible, sort_keys=True).encode()).hexdigest()[:16],
    }


def public_settings(config=None):
    config = runtime_settings() if config is None else config
    return {
        key: config[key]
        for key in (
            "support_email",
            "support_phone",
            "support_whatsapp",
            "support_help_url",
            "beta_open_date",
            "launch_date",
            "beta_registration_open",
        )
    }


def sender_identity(config=None):
    config = runtime_settings() if config is None else config
    return formataddr((config["email_sender_name"], config["email_from_address"]))


def beta_open_date(config=None):
    config = runtime_settings() if config is None else config
    return date.fromisoformat(config["beta_open_date"])


def safe_assistant_url(value):
    parsed = urlsplit(value)
    try:
        origin = f"{parsed.scheme}://{parsed.netloc}"
        valid = (
            parsed.scheme == "https"
            and parsed.hostname
            and not parsed.username
            and not parsed.password
            and parsed.port in (None, 443)
            and not parsed.query
            and not parsed.fragment
            and origin in assistant_origins()
        )
    except ValueError:
        valid = False
    return bool(valid)
