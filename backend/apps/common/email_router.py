"""Global Google-first routing, below recipient guards and shared by every mail caller."""

import base64
from datetime import timedelta

from django.conf import settings
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.db import connection, transaction
from django.db.models import Sum
from django.utils import timezone

from .models import EmailRoutingLock, EmailUsageBucket
from .provider_http import ProviderRejected, post_json


class EmailQuotaExceeded(Exception):
    pass


class EmailDeliveryUnknown(Exception):
    """A send may have succeeded. Callers must not automatically resend it."""


def reserve_provider(recipients, now=None, *, allow_fallback=True):
    """Reserve before I/O. Hour buckets conservatively retain up to 25 hours of usage.

    Count recipients rather than SMTP messages. Failed/uncertain attempts retain their
    reservation. No network operation or cross-provider retry happens under this lock.
    """
    now = now or timezone.now()
    hour = now.replace(minute=0, second=0, microsecond=0)
    # PostgreSQL is the deployment database. A second connection prevents a
    # caller's outer transaction from retaining this global lock during SMTP.
    # SQLite is supported for isolated local tests, not concurrent mail workers.
    alias = "email_quota" if connection.vendor == "postgresql" else "default"
    locks = EmailRoutingLock.objects.using(alias)
    buckets = EmailUsageBucket.objects.using(alias)
    locks.get_or_create(pk=1)
    with transaction.atomic(using=alias):
        locks.select_for_update().get(pk=1)
        from apps.audit.runtime_settings import runtime_settings

        limit = min(settings.EMAIL_GOOGLE_LIMIT, runtime_settings(alias=alias)["email_daily_limit"])
        recent = hour - timedelta(hours=24)
        used = dict(
            buckets.filter(hour__gte=recent)
            .values("provider")
            .annotate(total=Sum("recipients"))
            .values_list("provider", "total")
        )
        provider = "google"
        if used.get("google", 0) + recipients > limit:
            if not allow_fallback:
                raise EmailQuotaExceeded("Email allowance reached; messages must wait.")
            if not settings.RESEND_API_KEY or not settings.RESEND_FROM_EMAIL:
                raise EmailQuotaExceeded("Email quota reached; Resend is not configured.")
            month = hour.replace(day=1, hour=0)
            monthly = (
                buckets.filter(provider="resend", hour__gte=month).aggregate(
                    total=Sum("recipients")
                )["total"]
                or 0
            )
            if (
                used.get("resend", 0) + recipients > settings.RESEND_DAILY_LIMIT
                or monthly + recipients > settings.RESEND_MONTHLY_LIMIT
            ):
                raise EmailQuotaExceeded("Resend quota reached.")
            provider = "resend"
        bucket, created = buckets.get_or_create(provider=provider, hour=hour)
        bucket.recipients += recipients
        bucket.save(using=alias, update_fields=["recipients"])
        if created:
            # Operational counters only, bounded to the current/recent month.
            buckets.filter(hour__lt=hour - timedelta(days=35)).delete()
    return provider


def resend_payload(message):
    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": message.to,
        "subject": message.subject,
        "html" if message.content_subtype == "html" else "text": message.body,
    }
    for field in ("cc", "bcc", "reply_to"):
        if getattr(message, field):
            payload[field] = getattr(message, field)
    for alternative in getattr(message, "alternatives", []):
        if alternative[1] == "text/html":
            payload["html"] = alternative[0]
    attachments = []
    for part in message.message().walk():
        if part.is_multipart() or not part.get_filename():
            continue
        attachments.append(
            {
                "filename": part.get_filename(),
                "content": base64.b64encode(part.get_payload(decode=True)).decode(),
            }
        )
    if attachments:
        payload["attachments"] = attachments
    return payload


class EmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.managed_connection = False
        self.inner = get_connection(settings.EMAIL_PRIMARY_BACKEND, fail_silently=False, **kwargs)

    def open(self):
        # Open SMTP only after routing; a broken Google connection must not block Resend.
        self.managed_connection = True
        return True

    def close(self):
        self.managed_connection = False
        return self.inner.close()

    def send_messages(self, email_messages):
        try:
            return self._send_messages(email_messages)
        finally:
            if not self.managed_connection:
                try:
                    self.inner.close()
                except Exception:
                    # Cleanup cannot turn a successful send into a retryable error.
                    pass

    def _send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            if not message.recipients():
                continue
            try:
                provider = reserve_provider(len(message.recipients()))
                message.dwella_provider = provider
                try:
                    if provider == "google":
                        # Keep one SMTP connection for this batch; unmanaged single
                        # sends close it in send_messages' finally block.
                        self.inner.open()
                        accepted = self.inner.send_messages([message])
                    else:
                        result = post_json(
                            "https://api.resend.com/emails",
                            resend_payload(message),
                            {"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                        )
                        message.dwella_provider_id = result["id"]
                        accepted = 1
                except Exception as error:
                    if isinstance(error, ProviderRejected):
                        raise
                    raise EmailDeliveryUnknown("Email send needs review.") from None
                sent += accepted or 0
            except Exception:
                # Never fall back after an uncertain send: it could send twice.
                if not self.fail_silently:
                    raise
        return sent
