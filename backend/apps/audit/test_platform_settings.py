import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent, PlatformSettings

URL = "/api/v1/platform/settings/"


@pytest.mark.django_db
def test_default_disabled_and_admin_toggle_audited(settings):
    settings.HANDY_AGENT_URL = "https://assistant.example.com/agent"
    settings.HANDY_AGENT_SIGNING_SECRET = "test-platform-settings-signing-key-with-32-chars"
    client = APIClient()
    admin = get_user_model().objects.create_superuser(
        "admin", "admin@example.com", "StrongPass123!"
    )
    client.force_authenticate(admin)
    assert client.get(URL).data == {
        "handy_agent_enabled": False, "handy_agent_configured": True,
    }
    assert client.patch(URL, {"handy_agent_enabled": True}, format="json").status_code == 200
    assert PlatformSettings.objects.get(pk=1).handy_agent_enabled
    assert AuditEvent.objects.filter(action="platform.settings_updated").exists()
    invalid = client.patch(URL, {"handy_agent_enabled": {"bad": True}}, format="json")
    assert invalid.status_code == 400


@pytest.mark.django_db
def test_cannot_enable_unconfigured_assistant(settings):
    settings.HANDY_AGENT_URL = ""
    client = APIClient()
    admin = get_user_model().objects.create_superuser("admin", password="StrongPass123!")
    client.force_authenticate(admin)
    assert client.patch(URL, {"handy_agent_enabled": True}, format="json").status_code == 400
    assert not PlatformSettings.objects.filter(pk=1, handy_agent_enabled=True).exists()


@pytest.mark.django_db
def test_failed_audit_rolls_back_setting(monkeypatch, settings):
    settings.HANDY_AGENT_URL = "https://assistant.example.com/agent"
    settings.HANDY_AGENT_SIGNING_SECRET = "test-platform-settings-signing-key-with-32-chars"
    admin = get_user_model().objects.create_superuser("admin", password="StrongPass123!")
    PlatformSettings.objects.create(pk=1)
    client = APIClient()
    client.force_authenticate(admin)
    client.raise_request_exception = False

    def fail(*args, **kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr("apps.audit.settings_views.record_event", fail)
    assert client.patch(URL, {"handy_agent_enabled": True}, format="json").status_code == 500
    assert not PlatformSettings.objects.get(pk=1).handy_agent_enabled


@pytest.mark.django_db
def test_non_admin_cannot_change_or_read_settings():
    client = APIClient()
    assert client.get(URL).status_code == 403
    user = get_user_model().objects.create_user("manager", password="StrongPass123!")
    client.force_authenticate(user)
    assert client.get(URL).status_code == 403
    assert client.patch(URL, {"handy_agent_enabled": True}, format="json").status_code == 403


@pytest.mark.django_db
def test_disabled_blocks_tokens_and_existing_action_tokens(settings):
    from rest_framework.test import APIRequestFactory

    from apps.accounts.handy_agent import issue_handy_agent_token
    from apps.organizations.models import Organization, OrganizationMembership

    settings.HANDY_AGENT_SIGNING_SECRET = "test-platform-settings-signing-key-with-32-chars"
    user = get_user_model().objects.create_user("manager", password="StrongPass123!")
    org = Organization.objects.create(name="Test")
    OrganizationMembership.objects.create(user=user, organization=org, role="landlord")
    value = PlatformSettings.objects.create(pk=1, handy_agent_enabled=True)
    request = APIRequestFactory().post("/api/v1/accounts/handy-agent/token/")
    request.user = user
    token, _ = issue_handy_agent_token(user, request)
    value.handy_agent_enabled = False
    value.save()
    client = APIClient()
    client.force_authenticate(user)
    assert client.get("/api/v1/accounts/handy-agent/config/").data == {"enabled": False}
    assert client.post("/api/v1/accounts/handy-agent/token/").status_code == 403
    client.force_authenticate(user=None)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert client.post("/api/v1/assistant/properties/", {}, format="json").status_code in [401, 403]
