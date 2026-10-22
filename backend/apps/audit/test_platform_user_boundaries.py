import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import IdentityVerification

from .models import AuditEvent

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("authenticated", [False, True])
@pytest.mark.parametrize("method, suffix", [
    ("get", ""), ("post", ""), ("get", "{id}/"), ("patch", "{id}/"),
    ("delete", "{id}/"), ("post", "{id}/status/"), ("post", "{id}/membership/"),
    ("post", "{id}/admin-access/"), ("post", "{id}/password-reset/"),
    ("post", "{id}/sign-out/"), ("post", "{id}/reset-2fa/"),
])
def test_user_actions_deny_non_platform_actors(context, authenticated, method, suffix):
    client, _, _, _ = context
    target = get_user_model().objects.create_user(username="private-target")
    client.force_authenticate(target if authenticated else None)
    path = "/api/v1/platform/users/" + suffix.format(id=target.pk)
    response = getattr(client, method)(path, {}, format="json")
    assert response.status_code == 403
    assert not AuditEvent.objects.exists()
    target.refresh_from_db()
    assert target.is_active and not target.is_staff


@pytest.mark.parametrize("authenticated", [False, True])
@pytest.mark.parametrize("suffix, method", [("", "get"), ("{id}/", "get"),
                                        ("{id}/document/", "get"), ("{id}/review/", "post")])
def test_identity_routes_deny_non_platform_actors(context, authenticated, suffix, method):
    client, _, _, _ = context
    user = get_user_model().objects.create_user(username="private-applicant")
    check = IdentityVerification.objects.create(user=user, status="pending")
    client.force_authenticate(user if authenticated else None)
    response = getattr(client, method)(
        "/api/v1/platform/identity-verifications/" + suffix.format(id=check.pk),
        {"decision": "approved"}, format="json",
    )
    assert response.status_code == 403
    check.refresh_from_db()
    assert check.status == "pending"
    assert not AuditEvent.objects.exists()


@override_settings(REST_FRAMEWORK={
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"platform_write": "1/minute"},
})
def test_platform_write_throttle_blocks_before_account_mutation(context, monkeypatch):
    client, _, _, _ = context
    monkeypatch.setattr(ScopedRateThrottle, "THROTTLE_RATES", {"platform_write": "1/minute"})
    cache.clear()
    target = get_user_model().objects.create_user(username="limited-target")
    path = f"/api/v1/platform/users/{target.pk}/status/"
    assert client.post(path, {"active": False}, format="json").status_code == 200
    assert client.post(path, {"active": True}, format="json").status_code == 429
    target.refresh_from_db()
    assert not target.is_active
    assert AuditEvent.objects.filter(action="user.deactivated").count() == 1
