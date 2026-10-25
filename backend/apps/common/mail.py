"""Outbound recipient guard for staging and demos.

With APP_OUTBOUND_EMAIL_ALLOWLIST set, every email goes through
AllowlistEmailBackend, which drops recipients that are not listed before the
real backend sends. Entries are full addresses or "@domain". Test-only email
redirection instead sends every message to one configured inbox. This email
policy must not be reused as a phone/SMS/WhatsApp verification policy.
"""

import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.core.validators import validate_email

logger = logging.getLogger(__name__)
ALLOWLIST_BACKEND = "apps.common.mail.AllowlistEmailBackend"
LOCAL_ONLY_BACKENDS = {
    "django.core.mail.backends.console.EmailBackend",
    "django.core.mail.backends.dummy.EmailBackend",
}


def delivery_backend():
    """The backend that actually delivers, looking through the allowlist guard."""
    if settings.EMAIL_BACKEND == ALLOWLIST_BACKEND:
        return settings.OUTBOUND_INNER_EMAIL_BACKEND
    return settings.EMAIL_BACKEND


def delivery_configured():
    return delivery_backend() not in LOCAL_ONLY_BACKENDS


def email_redirect_recipient():
    recipient = getattr(settings, "TEST_EMAIL_REDIRECT_TO", "").strip()
    if not recipient:
        return ""
    if getattr(settings, "APP_ENVIRONMENT", "production") != "test":
        raise ImproperlyConfigured("Email redirection is restricted to test.")
    try:
        validate_email(recipient)
    except ValidationError as error:
        raise ImproperlyConfigured("Configure one valid test email recipient.") from error
    return recipient


def recipient_allowed(address, allowlist=None):
    if email_redirect_recipient():
        # Outbox checks may accept any intended email because the transport
        # will replace all envelope recipients with the single test inbox.
        return bool(address and "@" in str(address))
    allowlist = settings.OUTBOUND_EMAIL_ALLOWLIST if allowlist is None else allowlist
    if not allowlist:
        return True
    value = str(address or "").strip().casefold()
    # Keep only the address from "Name <user@example.com>".
    if "<" in value and value.endswith(">"):
        value = value[value.rindex("<") + 1 : -1]
    for entry in allowlist:
        entry = entry.strip().casefold()
        if entry.startswith("@") and value.endswith(entry):
            return True
        if entry and value == entry:
            return True
    return False


class AllowlistEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.redirect = email_redirect_recipient()
        self.inner = get_connection(
            settings.OUTBOUND_INNER_EMAIL_BACKEND, fail_silently=fail_silently, **kwargs
        )

    def open(self):
        return self.inner.open()

    def close(self):
        return self.inner.close()

    def send_messages(self, email_messages):
        allowed, dropped = [], 0
        for message in email_messages:
            if self.redirect:
                original = message.recipients()
                if not original:
                    continue
                message.extra_headers = {
                    key: value
                    for key, value in message.extra_headers.items()
                    if key.lower() not in {"to", "cc", "bcc"}
                }
                message.extra_headers.setdefault(
                    "X-Dwella-Original-Recipients", ", ".join(original)
                )
                message.to, message.cc, message.bcc = [self.redirect], [], []
                if not message.subject.startswith("[TEST] "):
                    message.subject = "[TEST] " + message.subject
                allowed.append(message)
                continue
            for field in ("to", "cc", "bcc"):
                kept = [a for a in getattr(message, field) if recipient_allowed(a)]
                dropped += len(getattr(message, field)) - len(kept)
                setattr(message, field, kept)
            if message.recipients():
                allowed.append(message)
        if dropped:
            # Counts only: recipient addresses stay out of logs.
            logger.info("Outbound allowlist withheld %s email recipient(s)", dropped)
        return self.inner.send_messages(allowed) if allowed else 0
