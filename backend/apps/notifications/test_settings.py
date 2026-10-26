# ruff: noqa: F811
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.organizations.models import Organization, OrganizationMembership
from apps.payments.testing import client_for, configuration, home  # noqa: F401

from .models import MessagingSettings, NotificationPreferences, ReminderPreferences

pytestmark = pytest.mark.django_db
BASE = "/api/v1/notifications/"


@pytest.mark.parametrize(
    "path", ["preferences/", "reminders/", "platform-settings/", "workspace-settings/"]
)
def test_settings_require_authentication(path):
    assert APIClient().get(BASE + path).status_code in {401, 403}
    assert APIClient().patch(BASE + path, {}, format="json").status_code in {401, 403}


def test_personal_preferences_are_private_and_changes_are_audited(home):
    client = client_for(home["manager"])
    response = client.patch(BASE + "preferences/", {"in_app_payment": False}, format="json")
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert not response.json()["response_data"]["preferences"]["in_app_payment"]
    other = client_for(home["tenant"]).get(BASE + "preferences/").json()["response_data"]
    assert other["preferences"]["in_app_payment"]
    # Reading shows defaults without creating a row.
    assert NotificationPreferences.objects.count() == 1
    assert AuditEvent.objects.filter(action="settings.preferences_updated").count() == 1
    assert (
        client.patch(BASE + "preferences/", {"user": home["tenant"].pk}, format="json").status_code
        == 400
    )


@pytest.mark.parametrize("channel", ["email", "sms", "whatsapp"])
def test_unconfigured_delivery_preferences_can_be_saved_without_sending(home, channel):
    client = client_for(home["manager"])
    with patch("django.core.mail.send_mail") as mail:
        for path in ["preferences/", "reminders/"]:
            response = client.patch(BASE + path, {f"{channel}_enabled": True}, format="json")
            assert response.status_code == 200
            assert response.json()["response_data"]["preferences"][f"{channel}_enabled"]
            assert not response.json()["response_data"]["channels"][channel]
        mail.assert_not_called()


def test_tenant_cannot_edit_workspace_or_platform_settings(home):
    for role in ["tenant", "manager"]:
        client = client_for(home[role])
        if role == "tenant":
            for path in ["reminders/", "workspace-settings/"]:
                assert client.get(BASE + path).status_code == 403
                assert client.patch(BASE + path, {}, format="json").status_code == 403
        assert client.get(BASE + "platform-settings/").status_code == 403
        assert client.patch(BASE + "platform-settings/", {}, format="json").status_code == 403
    staff = get_user_model().objects.create_user(username="ordinary-staff", is_staff=True)
    assert client_for(staff).get(BASE + "platform-settings/").status_code == 403


def test_reminders_are_scoped_and_validate_schedule(home):
    client = client_for(home["manager"])
    assert client.patch(BASE + "reminders/", {"due_hour": 24}, format="json").status_code == 400
    assert (
        client.patch(BASE + "reminders/", {"overdue_repeats": 4}, format="json").status_code == 400
    )
    assert client.patch(BASE + "reminders/", {"due_hour": 11}, format="json").status_code == 200
    assert ReminderPreferences.objects.get(organization=home["org"]).due_hour == 11
    other = Organization.objects.create(name="Other settings workspace")
    owner = get_user_model().objects.create_user(username="other-settings-owner")
    OrganizationMembership.objects.create(organization=other, user=owner, role="landlord")
    response = client_for(owner).get(BASE + "reminders/")
    assert response.json()["response_data"]["preferences"]["due_hour"] == 9
    assert (
        client.patch(BASE + "reminders/", {"organization": other.pk}, format="json").status_code
        == 400
    )
    home["org"].is_active = False
    home["org"].save()
    assert client.patch(BASE + "reminders/", {"due_hour": 12}, format="json").status_code == 403


def test_workspace_settings_validate_and_do_not_change_money_currency(home):
    client = client_for(home["manager"])
    url = BASE + "workspace-settings/"
    for data in [{"email": "bad"}, {"timezone": "not-a-zone"}, {"phone_number": "invalid"}]:
        assert client.patch(url, data, format="json").status_code == 400
    response = client.patch(url, {"display_name": "My rentals", "currency": "USD"}, format="json")
    assert response.status_code == 200
    home["org"].refresh_from_db()
    assert home["org"].display_name == "My rentals" and home["org"].currency == "ZMW"


def test_platform_limits_cannot_activate_sending_and_reject_bad_input(home):
    client = client_for(home["admin"])
    url = BASE + "platform-settings/"
    assert client.get(url).status_code == 200
    for body in [
        {"daily_cap": "25.00"},
        {"quiet_from": "bad"},
        {"sms_fallback": True},
        {"secret_key": "not-a-real-secret"},
        {"quiet_from": "07:00", "quiet_until": "07:00"},
    ]:
        assert client.patch(url, body, format="json").status_code == 400
    assert client.patch(url, ["bad"], format="json").status_code == 400
    assert client.patch(url, {"quiet_from": "21:00"}, format="json").status_code == 200
    value = MessagingSettings.objects.get(pk=1)
    assert str(value.quiet_from) == "21:00:00" and not value.reminders_enabled


def test_reading_settings_creates_nothing(home):
    for role, path in [("manager", "reminders/"), ("admin", "platform-settings/")]:
        assert client_for(home[role]).get(BASE + path).status_code == 200
    assert not ReminderPreferences.objects.exists()
    assert not MessagingSettings.objects.exists()


def test_settings_write_throttle(home):
    client = client_for(home["manager"])
    cache.clear()
    with patch("apps.notifications.settings_views.SettingsWriteThrottle.rate", "1/minute"):
        assert client.patch(BASE + "preferences/", {}, format="json").status_code == 200
        assert client.patch(BASE + "preferences/", {}, format="json").status_code == 429
    cache.clear()


def test_in_app_preferences_filter_optional_alerts_but_preserve_overdue_notices(home):
    NotificationPreferences.objects.create(
        user=home["manager"], in_app_payment=False, in_app_lease=False
    )
    alerts = [
        {"id": "payment:demo", "kind": "payment"},
        {"id": "lease:demo", "kind": "lease"},
        {"id": "invoice:demo", "kind": "arrears"},
        {"id": "payout:demo", "kind": "payment"},
    ]
    with patch("apps.notifications.views.live_alerts", return_value=alerts):
        data = client_for(home["manager"]).get(BASE).json()["response_data"]
    assert [item["id"] for item in data["items"]] == ["invoice:demo", "payout:demo"]
