from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.mail import EmailMessage, EmailMultiAlternatives, get_connection
from django.db import connection, transaction
from django.test import override_settings
from django.utils import timezone

from .email_router import EmailDeliveryUnknown, EmailQuotaExceeded, reserve_provider
from .models import EmailUsageBucket

pytestmark = pytest.mark.django_db(transaction=True, databases=["default", "email_quota"])
ROUTING = {
    "EMAIL_BACKEND": "apps.common.email_router.EmailBackend",
    "EMAIL_PRIMARY_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "EMAIL_GOOGLE_LIMIT": 2,
    "RESEND_API_KEY": "test-only",
    "RESEND_FROM_EMAIL": "Dwella <notify@example.com>",
    "RESEND_DAILY_LIMIT": 100,
    "RESEND_MONTHLY_LIMIT": 3000,
}


@override_settings(**ROUTING)
def test_global_routing_counts_account_signing_and_reminder_recipients():
    from apps.accounts.account_mail import send_account_mail

    assert send_account_mail("Account", "Confirm account", "a@example.com")
    assert EmailMessage("Signing", "Lease", to=["b@example.com"]).send() == 1
    with patch("apps.common.email_router.post_json", return_value={"id": "resend-1"}) as api:
        message = EmailMessage("Reminder", "Rent", to=["c@example.com"])
        assert message.send() == 1
    assert len(mail.outbox) == 2
    assert message.dwella_provider == "resend" and message.dwella_provider_id == "resend-1"
    assert api.call_args.args[1]["from"] == ROUTING["RESEND_FROM_EMAIL"]
    assert sum(EmailUsageBucket.objects.values_list("recipients", flat=True)) == 3


@override_settings(**ROUTING)
def test_routed_batches_reuse_smtp_and_single_sends_close_the_connection():
    with override_settings(
        EMAIL_PRIMARY_BACKEND="django.core.mail.backends.smtp.EmailBackend",
        EMAIL_GOOGLE_LIMIT=20,
        EMAIL_USE_TLS=False,
        EMAIL_USE_SSL=False,
        EMAIL_HOST_USER="",
    ):
        with patch("django.core.mail.backends.smtp.smtplib.SMTP") as smtp:
            with get_connection() as transport:
                assert transport.send_messages([EmailMessage("A", "B", to=["a@example.com"])]) == 1
                assert transport.send_messages([EmailMessage("C", "D", to=["b@example.com"])]) == 1
                assert smtp.call_count == 1
                smtp.return_value.quit.assert_not_called()
            smtp.return_value.quit.assert_called_once()
        with patch("django.core.mail.backends.smtp.smtplib.SMTP") as smtp:
            assert EmailMessage("A", "B", to=["a@example.com"]).send() == 1
            smtp.return_value.quit.assert_called_once()


@override_settings(**ROUTING)
def test_to_cc_bcc_count_and_quota_exhaustion_never_calls_network():
    assert reserve_provider(2) == "google"
    with override_settings(RESEND_DAILY_LIMIT=2):
        assert reserve_provider(2) == "resend"
        with pytest.raises(EmailQuotaExceeded):
            reserve_provider(1)
    with override_settings(RESEND_API_KEY=""):
        with pytest.raises(EmailQuotaExceeded):
            reserve_provider(1)


@override_settings(**ROUTING)
def test_monthly_limit_and_rolling_window_and_retention():
    now = timezone.now().replace(day=15, hour=12)
    assert reserve_provider(2, now=now) == "google"
    with override_settings(RESEND_MONTHLY_LIMIT=1):
        assert reserve_provider(1, now=now) == "resend"
        with pytest.raises(EmailQuotaExceeded):
            reserve_provider(1, now=now)
    assert reserve_provider(2, now=now + timedelta(hours=26)) == "google"
    reserve_provider(1, now=now + timedelta(days=40))
    assert not EmailUsageBucket.objects.filter(hour__lt=now + timedelta(days=5)).exists()


@override_settings(**ROUTING)
def test_smtp_uncertainty_does_not_fall_back_or_release_reservation():
    with patch(
        "django.core.mail.backends.locmem.EmailBackend.send_messages", side_effect=TimeoutError
    ):
        with patch("apps.common.email_router.post_json") as api:
            with pytest.raises(EmailDeliveryUnknown):
                EmailMessage("Lease", "Body", to=["a@example.com"]).send()
    api.assert_not_called()
    assert EmailUsageBucket.objects.get(provider="google").recipients == 1


@override_settings(**ROUTING)
def test_guard_redirects_before_resend_including_cc_bcc_html_and_pdf():
    with override_settings(
        EMAIL_BACKEND="apps.common.mail.AllowlistEmailBackend",
        OUTBOUND_INNER_EMAIL_BACKEND=ROUTING["EMAIL_BACKEND"],
        APP_ENVIRONMENT="test",
        TEST_EMAIL_REDIRECT_TO="sink@example.com",
        EMAIL_GOOGLE_LIMIT=0,
    ):
        message = EmailMultiAlternatives(
            "Lease",
            "Plain",
            to=["tenant@example.com"],
            cc=["cc@example.com"],
            bcc=["secret@example.com"],
            reply_to=["owner@example.com"],
        )
        message.attach_alternative("<p>Lease</p>", "text/html")
        message.attach("lease.pdf", b"%PDF-test", "application/pdf")
        with patch("apps.common.email_router.post_json", return_value={"id": "email-1"}) as api:
            assert message.send() == 1
        payload = api.call_args.args[1]
        assert (
            payload["to"] == ["sink@example.com"] and "cc" not in payload and "bcc" not in payload
        )
        assert payload["html"] == "<p>Lease</p>" and payload["subject"] == "[TEST] Lease"
        assert payload["attachments"][0]["filename"] == "lease.pdf"
        assert EmailUsageBucket.objects.get().recipients == 1


@override_settings(**ROUTING)
def test_provider_io_happens_after_quota_transaction_commits():
    def response(*args):
        assert not connection.in_atomic_block
        return {"id": "email-1"}

    with override_settings(EMAIL_GOOGLE_LIMIT=0):
        with patch("apps.common.email_router.post_json", side_effect=response):
            assert EmailMessage("Notice", "Body", to=["a@example.com"]).send() == 1


@override_settings(**ROUTING)
def test_postgres_reservation_survives_callers_rollback_and_releases_its_lock():
    if connection.vendor != "postgresql":
        pytest.skip("Independent PostgreSQL quota connection required.")
    from django.db import connections

    with pytest.raises(RuntimeError):
        with transaction.atomic():
            reserve_provider(1)
            assert not connections["email_quota"].in_atomic_block
            raise RuntimeError("Account transaction rolled back after an uncertain send.")
    assert EmailUsageBucket.objects.get().recipients == 1


@override_settings(**ROUTING)
def test_postgres_concurrent_workers_cannot_overspend_google_quota():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks required.")
    from concurrent.futures import ThreadPoolExecutor

    from django.db import connections

    def reserve(_):
        try:
            return reserve_provider(1)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=4) as pool:
        providers = list(pool.map(reserve, range(8)))
    assert providers.count("google") == 2 and providers.count("resend") == 6
