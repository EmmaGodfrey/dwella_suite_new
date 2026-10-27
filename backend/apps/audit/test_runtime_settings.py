import socket
import ssl
from datetime import timedelta
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework import serializers
from rest_framework.test import APIClient

from apps.accounts.handy_agent import handy_agent_enabled
from apps.marketing.emails import beta_open_date, countdown_windows, due_steps
from apps.marketing.models import BetaApplication

from .models import AuditEvent, PlatformSettings
from .runtime_settings import runtime_settings
from .runtime_views import PinnedHTTPSConnection, verify_assistant_connection

URL = "/api/v1/platform/runtime-settings/"
CHECK = URL + "assistant-check/"
NEW = "https://dwella.agents.handyagent.chat"
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_limits():
    cache.clear()


@pytest.fixture
def admin():
    user = get_user_model().objects.create_superuser("runtime-admin", password=None)
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_read_is_bounded_private_and_does_not_create_settings(admin, settings):
    settings.WHATSAPP_ACCESS_TOKEN = "private-whatsapp-token-never-expose"
    settings.HANDY_AGENT_SIGNING_SECRET = "private-signing-key-never-expose"
    with CaptureQueriesContext(connection) as queries:
        result = admin.get(URL)
    assert result.status_code == 200
    assert result["Cache-Control"] == "private, no-store"
    assert not PlatformSettings.objects.exists()
    assert not any(q["sql"].lstrip().startswith(("INSERT", "UPDATE")) for q in queries)
    assert len(queries) <= 4
    assert settings.WHATSAPP_ACCESS_TOKEN not in str(result.data)
    assert settings.HANDY_AGENT_SIGNING_SECRET not in str(result.data)
    assert not any("resend" in key for key in result.data["values"])


@pytest.mark.parametrize("path", [URL, CHECK])
def test_only_system_admin_can_read_or_write(path):
    client = APIClient()
    for user in (None, get_user_model().objects.create_user("ordinary", password=None)):
        client.force_authenticate(user)
        with patch("apps.audit.runtime_views.verify_assistant_connection") as check:
            for method in ("get", "patch", "post"):
                result = getattr(client, method)(path, {}, format="json")
                assert result.status_code == 403
            check.assert_not_called()
    assert not PlatformSettings.objects.exists()


@pytest.mark.parametrize(
    "values",
    [
        {"email_daily_limit": 0},
        {"email_daily_limit": 401},
        {"email_daily_limit": "many"},
        {"email_sender_name": "Dwella\r\nBcc: bad@example.com"},
        {"email_from_address": "unapproved@example.com"},
        {"support_help_url": "http://example.com"},
        {"support_whatsapp": "not-a-phone"},
        {"assistant_url": "http://dwella.agents.handyagent.chat"},
        {"assistant_url": "https://evil.example/"},
        {"assistant_url": NEW + "/?token=x"},
        {"assistant_url": "https://user:password@dwella.agents.handyagent.chat"},
        {"beta_countdown_days": [1, 7, 14]},
        {"beta_countdown_days": [14, 7, 7]},
        {"beta_open_date": "bad-date"},
        {"beta_send_hour": 24},
        {"launch_date": "2026-01-01"},
        {"resend_daily_limit": 100},
        {"runtime_config": {"assistant_verified_url": NEW}},
        {"HANDY_AGENT_SIGNING_SECRET": "replacement"},
    ],
)
def test_invalid_and_unsupported_fields_are_rejected_without_mutation(admin, values):
    result = admin.patch(URL, values, format="json")
    assert result.status_code == 400
    assert not PlatformSettings.objects.exists()
    assert not AuditEvent.objects.filter(action="platform.runtime_settings_updated").exists()


@pytest.mark.parametrize(
    "field", ["messaging_email_enabled", "beta_emails_enabled", "sms_enabled", "whatsapp_enabled"]
)
def test_cannot_activate_unconfigured_delivery(admin, settings, field):
    settings.EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"
    settings.AFRICASTALKING_API_KEY = ""
    settings.WHATSAPP_ACCESS_TOKEN = ""
    assert admin.patch(URL, {field: True}, format="json").status_code == 400


def test_sender_and_phone_provider_metadata_apply_with_server_credentials(admin, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.APPROVED_EMAIL_SENDERS = ["approved@example.com"]
    settings.AFRICASTALKING_USERNAME = "synthetic"
    settings.AFRICASTALKING_API_KEY = "synthetic-key"
    settings.AFRICASTALKING_CALLBACK_TOKEN = "x" * 32
    settings.APPROVED_SMS_SENDERS = ["DWELLA"]
    result = admin.patch(
        URL,
        {
            "email_from_address": "approved@example.com",
            "email_sender_name": "Dwella support",
            "email_reply_to": "reply@example.com",
            "sms_sender_id": "DWELLA",
            "sms_enabled": True,
        },
        format="json",
    )
    assert result.status_code == 200
    from apps.notifications.phone_messaging import sms_ready

    assert sms_ready()
    assert runtime_settings()["email_sender_name"] == "Dwella support"
    assert AuditEvent.objects.filter(action="platform.runtime_settings_updated").exists()
    settings.APPROVED_SMS_SENDERS = []
    assert admin.patch(URL, {"sms_sender_id": "UNAPPROVED"}, format="json").status_code == 400


def test_changes_roll_back_if_audit_cannot_be_saved(admin):
    admin.raise_request_exception = False
    with patch("apps.audit.runtime_views.record_event", side_effect=RuntimeError("audit")):
        result = admin.patch(URL, {"support_email": "support@example.com"}, format="json")
    assert result.status_code == 500
    assert not PlatformSettings.objects.exists()


def test_new_assistant_address_disables_until_verified(admin, settings):
    settings.HANDY_AGENT_URL = "https://dwella.handyagents.wazabanda.dev/agent"
    settings.HANDY_AGENT_SIGNING_SECRET = "x" * 32
    PlatformSettings.objects.create(pk=1, handy_agent_enabled=True)
    assert admin.patch(URL, {"assistant_url": NEW}, format="json").status_code == 200
    assert not handy_agent_enabled()
    assert (
        admin.patch(
            "/api/v1/platform/settings/", {"handy_agent_enabled": True}, format="json"
        ).status_code
        == 400
    )
    with patch("apps.audit.runtime_views.verify_assistant_connection") as check:
        assert admin.post(CHECK, {}, format="json").status_code == 200
        check.assert_called_once_with(NEW)
    assert not handy_agent_enabled()  # Checking is not enabling.
    assert (
        admin.patch(
            "/api/v1/platform/settings/", {"handy_agent_enabled": True}, format="json"
        ).status_code
        == 200
    )
    config = admin.get("/api/v1/accounts/handy-agent/config/").data
    assert config["enabled"] and config["url"] == NEW and config["revision"]


def test_tls_failure_never_records_verification(admin):
    admin.patch(URL, {"assistant_url": NEW}, format="json")
    with patch(
        "apps.audit.runtime_views.verify_assistant_connection",
        side_effect=serializers.ValidationError({"assistant_url": "HTTPS verification failed."}),
    ):
        assert admin.post(CHECK, {}, format="json").status_code == 400
    assert "assistant_verified_url" not in PlatformSettings.objects.get().runtime_config


def test_check_rejects_an_address_changed_during_network_io(admin):
    admin.patch(URL, {"assistant_url": NEW}, format="json")

    def change(_):
        instance = PlatformSettings.objects.get()
        instance.runtime_config = {"assistant_url": NEW + "/different"}
        instance.save()

    with patch("apps.audit.runtime_views.verify_assistant_connection", side_effect=change):
        assert admin.post(CHECK, {}, format="json").status_code == 400
    assert "assistant_verified_url" not in PlatformSettings.objects.get().runtime_config


def test_connection_verifier_does_not_send_auth_or_follow_redirects():
    address = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
    response = Mock(status=200)
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    opener = Mock()
    opener.open.return_value = response
    with (
        patch("apps.audit.runtime_views.socket.getaddrinfo", return_value=address),
        patch("apps.audit.runtime_views.build_opener", return_value=opener),
    ):
        verify_assistant_connection(NEW)
        request = opener.open.call_args.args[0]
        assert not request.has_header("Authorization")
        assert not request.has_header("Cookie")
        for error in (
            URLError(ssl.SSLCertVerificationError("self signed")),
            HTTPError(NEW, 302, "redirect", {}, None),
        ):
            opener.open.side_effect = error
            with pytest.raises(serializers.ValidationError):
                verify_assistant_connection(NEW)


def test_connection_check_rejects_private_addresses_before_http():
    address = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
    with (
        patch("apps.audit.runtime_views.socket.getaddrinfo", return_value=address),
        patch("apps.audit.runtime_views.build_opener") as opener,
    ):
        with pytest.raises(serializers.ValidationError):
            verify_assistant_connection(NEW)
        opener.assert_not_called()


def test_public_config_exposes_only_public_contacts_and_dates(admin):
    assert (
        admin.patch(
            URL,
            {"support_email": "help@example.com", "beta_open_date": "2026-12-01"},
            format="json",
        ).status_code
        == 200
    )
    result = APIClient().get("/api/v1/marketing/configuration/")
    assert result.status_code == 200
    assert set(result.data) == {
        "support_email",
        "support_phone",
        "support_whatsapp",
        "support_help_url",
        "beta_open_date",
        "launch_date",
        "beta_registration_open",
    }
    assert result.data["beta_open_date"] == beta_open_date().isoformat() == "2026-12-01"
    assert APIClient().get("/api/v1/accounts/register/").data["beta_open_date"] == "2026-12-01"
    assert countdown_windows()[0][1].isoformat() == "2026-11-17"


def test_resume_does_not_release_old_missed_beta_steps(admin, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.BETA_EMAILS_ENABLED = False
    application = BetaApplication.objects.create(
        name="Older signup", phone="000", email="old@example.com", units="1"
    )
    before = timezone.now() - timedelta(days=30)
    BetaApplication.objects.filter(pk=application.pk).update(created_at=before)
    application.refresh_from_db()
    assert admin.patch(URL, {"beta_emails_enabled": True}, format="json").status_code == 200
    assert due_steps(application) == []


def test_settings_writes_are_rate_limited(admin):
    for _ in range(30):
        assert admin.patch(URL, {"support_phone": ""}, format="json").status_code == 200
    assert admin.patch(URL, {"support_phone": ""}, format="json").status_code == 429


def test_connection_pins_checked_ip_and_keeps_hostname_verification():
    context, raw = Mock(), Mock()
    connection = PinnedHTTPSConnection(
        "dwella.agents.handyagent.chat", pinned_ip="93.184.216.34", context=context, timeout=5
    )
    with patch("apps.audit.runtime_views.socket.create_connection", return_value=raw) as connect:
        connection.connect()
    assert connect.call_args.args[0] == ("93.184.216.34", 443)
    context.wrap_socket.assert_called_once_with(
        raw, server_hostname="dwella.agents.handyagent.chat"
    )
    context.wrap_socket.side_effect = ssl.SSLError("invalid certificate")
    with patch("apps.audit.runtime_views.socket.create_connection", return_value=raw):
        with pytest.raises(ssl.SSLError):
            connection.connect()
    raw.close.assert_called_once()


@pytest.mark.django_db(transaction=True)
def test_connection_network_check_holds_no_transaction(admin):
    assert admin.patch(URL, {"assistant_url": NEW}, format="json").status_code == 200

    def check(_):
        assert not connection.in_atomic_block

    with patch("apps.audit.runtime_views.verify_assistant_connection", side_effect=check):
        assert admin.post(CHECK, {}, format="json").status_code == 200


def test_public_configuration_has_one_row_read():
    with CaptureQueriesContext(connection) as queries:
        assert APIClient().get("/api/v1/marketing/configuration/").status_code == 200
    assert len(queries) == 1


def test_runtime_configuration_table_is_private_on_postgres():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row security")
    with connection.cursor() as cursor:
        cursor.execute("SELECT relrowsecurity FROM pg_class WHERE relname='audit_platformsettings'")
        assert cursor.fetchone() == (True,)
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='handy_agent'")
        if cursor.fetchone():
            cursor.execute(
                "SELECT has_table_privilege('handy_agent', 'audit_platformsettings', 'SELECT')"
            )
            assert not cursor.fetchone()[0]
