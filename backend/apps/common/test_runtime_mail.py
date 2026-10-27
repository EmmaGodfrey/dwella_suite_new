from unittest.mock import patch

import pytest
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMessage, get_connection
from django.db import connections

from apps.audit.models import PlatformSettings

from .email_router import EmailDeliveryUnknown, EmailQuotaExceeded
from .models import EmailUsageBucket

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "email_quota"])


@pytest.fixture(autouse=True)
def close_mirror():
    yield
    connections["email_quota"].close()


@pytest.fixture
def runtime_mail(settings):
    settings.EMAIL_BACKEND = "apps.common.runtime_mail.RuntimeEmailBackend"
    settings.RUNTIME_MAIL_INNER_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.DEFAULT_FROM_EMAIL = "original@example.com"
    settings.APPROVED_EMAIL_SENDERS = ["approved@example.com"]
    settings.EMAIL_GOOGLE_LIMIT = 400
    PlatformSettings.objects.create(
        pk=1,
        runtime_config={
            "email_sender_name": "Dwella support",
            "email_from_address": "approved@example.com",
            "email_reply_to": "reply@example.com",
            "email_daily_limit": 2,
        },
    )
    return settings


def test_shared_smtp_limit_and_identity_apply_to_all_messages(runtime_mail):
    with get_connection() as connection:
        for _ in range(2):
            message = EmailMessage(
                "Synthetic",
                "Body",
                runtime_mail.DEFAULT_FROM_EMAIL,
                ["to@example.com"],
                connection=connection,
            )
            assert message.send() == 1
        with pytest.raises(EmailQuotaExceeded):
            EmailMessage(
                "Third",
                "Body",
                runtime_mail.DEFAULT_FROM_EMAIL,
                ["to@example.com"],
                connection=connection,
            ).send()
    assert len(mail.outbox) == 2
    assert all(row.from_email == "Dwella support <approved@example.com>" for row in mail.outbox)
    assert all(row.reply_to == ["reply@example.com"] for row in mail.outbox)
    assert EmailUsageBucket.objects.get(provider="google").recipients == 2


def test_no_resend_fallback_is_added_for_smtp(runtime_mail):
    runtime_mail.RESEND_API_KEY = "synthetic-unused"
    runtime_mail.RESEND_FROM_EMAIL = "other@example.com"
    message = EmailMessage(
        "Synthetic",
        "Body",
        runtime_mail.DEFAULT_FROM_EMAIL,
        ["one@example.com", "two@example.com", "three@example.com"],
    )
    with pytest.raises(EmailQuotaExceeded):
        message.send()
    assert not EmailUsageBucket.objects.filter(provider="resend").exists()


def test_recipient_guards_run_before_shared_budget(runtime_mail):
    runtime_mail.EMAIL_BACKEND = "apps.common.mail.AllowlistEmailBackend"
    runtime_mail.OUTBOUND_INNER_EMAIL_BACKEND = "apps.common.runtime_mail.RuntimeEmailBackend"
    runtime_mail.OUTBOUND_EMAIL_ALLOWLIST = ["allowed@example.com"]
    EmailMessage("Guarded", "Body", runtime_mail.DEFAULT_FROM_EMAIL, ["blocked@example.com"]).send()
    assert not EmailUsageBucket.objects.exists()
    assert not mail.outbox


def test_uncertain_smtp_is_not_retryable_and_keeps_reservation(runtime_mail):
    connection = get_connection()
    with patch.object(connection.inner, "send_messages", side_effect=OSError("uncertain")) as send:
        with pytest.raises(EmailDeliveryUnknown):
            EmailMessage(
                "Uncertain",
                "Body",
                runtime_mail.DEFAULT_FROM_EMAIL,
                ["one@example.com"],
                connection=connection,
            ).send()
    assert send.call_count == 1
    assert EmailUsageBucket.objects.get(provider="google").recipients == 1


def test_revoked_sender_stops_before_quota_or_delivery(runtime_mail):
    runtime_mail.APPROVED_EMAIL_SENDERS = []
    with pytest.raises(ImproperlyConfigured):
        EmailMessage("Blocked", "Body", runtime_mail.DEFAULT_FROM_EMAIL, ["one@example.com"]).send()
    assert not EmailUsageBucket.objects.exists()
    assert not mail.outbox
