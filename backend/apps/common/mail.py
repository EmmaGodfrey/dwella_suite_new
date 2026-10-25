"""Outbound recipient guard for staging and demos.

With APP_OUTBOUND_EMAIL_ALLOWLIST set, every email goes through
AllowlistEmailBackend, which drops recipients that are not listed before the
real backend sends. Entries are full addresses or "@domain". SMS and WhatsApp
senders must call recipient_allowed() the same way before sending.
"""

import logging

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend

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


def recipient_allowed(address, allowlist=None):
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
