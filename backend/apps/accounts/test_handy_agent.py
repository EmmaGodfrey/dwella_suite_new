from datetime import UTC, timedelta

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership

User = get_user_model()
URL = "/api/v1/accounts/handy-agent/token/"
SECRET = "test-handy-agent-signing-secret-with-32-chars"
@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()


@pytest.fixture(autouse=True)
def enable_assistant(db):
    from apps.audit.models import PlatformSettings
    PlatformSettings.objects.create(pk=1, handy_agent_enabled=True)


def authenticated_client(user):
    client = APIClient()
    token = Token.objects.create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


def member(role):
    user = User.objects.create_user(
        username=f"{role}@example.com",
        email=f"{role}@example.com",
        password="StrongerPass123",
        first_name=role.title(),
    )
    organization = Organization.objects.create(name=f"{role.title()} Estates")
    OrganizationMembership.objects.create(organization=organization, user=user, role=role)
    return user, organization


@pytest.mark.django_db
@override_settings(
    HANDY_AGENT_SIGNING_SECRET=SECRET,
    HANDY_AGENT_ISSUER="https://api.dwella.properties",
    HANDY_AGENT_AUDIENCE="handy-agent",
    HANDY_AGENT_TOKEN_TTL_SECONDS=900,
)
@pytest.mark.parametrize(
    ("role", "expected_groups", "expected_actor"),
    [
        ("landlord", ["organization_admin", "portfolio_manager", "portfolio_viewer"], True),
    ],
)
def test_issues_scoped_short_lived_token_for_supported_roles(
    role, expected_groups, expected_actor
):
    user, organization = member(role)

    response = authenticated_client(user).post(URL)

    assert response.status_code == 200
    claims = jwt.decode(
        response.data["token"],
        SECRET,
        algorithms=["HS256"],
        audience="handy-agent",
        issuer="https://api.dwella.properties",
    )
    assert claims["sub"] == str(user.pk)
    assert claims["groups"] == expected_groups
    assert claims["attrs"] == {"organization_ids": [organization.pk]}
    assert claims["agent"] == {
        "thinker": True,
        "actor": expected_actor,
        "ledger": False,
    }
    assert response.data["host_authorization"] == f"Bearer {response.data['token']}"
    assert timedelta(minutes=14, seconds=55) <= (
        timezone.datetime.fromtimestamp(claims["exp"], tz=UTC) - timezone.now()
    ) <= timedelta(minutes=15)


@pytest.mark.django_db
@override_settings(HANDY_AGENT_SIGNING_SECRET=SECRET)
def test_platform_admin_token_has_no_workspace_data_without_support_session():
    user = User.objects.create_superuser(
        username="platform@example.com",
        email="platform@example.com",
        password="StrongerPass123",
    )

    response = authenticated_client(user).post(URL)
    claims = jwt.decode(
        response.data["token"],
        SECRET,
        algorithms=["HS256"],
        audience="handy-agent",
        issuer="https://api.dwella.properties",
    )

    assert claims["groups"] == ["platform_admin"]
    assert claims["attrs"] == {"organization_ids": []}


@pytest.mark.django_db
@override_settings(HANDY_AGENT_SIGNING_SECRET=SECRET)
@pytest.mark.parametrize("role", ["tenant", None])
def test_rejects_unsupported_accounts(role):
    if role:
        user, _ = member(role)
    else:
        user = User.objects.create_user(username="unassigned", password="StrongerPass123")

    response = authenticated_client(user).post(URL)

    assert response.status_code == 403


@pytest.mark.django_db
def test_requires_authentication():
    assert APIClient().post(URL).status_code == 403


@pytest.mark.django_db
@override_settings(HANDY_AGENT_SIGNING_SECRET="")
def test_returns_service_unavailable_without_a_strong_signing_secret():
    user, _ = member("landlord")

    response = authenticated_client(user).post(URL)

    assert response.status_code == 503


@pytest.mark.django_db
@override_settings(HANDY_AGENT_SIGNING_SECRET=SECRET)
def test_rate_limits_repeated_token_issuance():
    user, _ = member("landlord")
    client = authenticated_client(user)

    for _ in range(20):
        assert client.post(URL).status_code == 200
    assert client.post(URL).status_code == 429
