import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.organizations.models import OrganizationMembership

pytestmark = pytest.mark.django_db
URL = "/api/v1/accounts/register/"
PAYLOAD = {
    "first_name": "Moses",
    "last_name": "Chileshe",
    "email": "moses@example.com",
    "password": "Lakeview9!Permanent",
}


@pytest.fixture(autouse=True)
def registration_settings(settings):
    settings.BETA_REGISTRATION_OPEN = True
    cache.clear()
    yield
    cache.clear()


def test_signup_cannot_grant_platform_or_workspace_privileges():
    client = APIClient()
    response = client.post(
        URL,
        {
            **PAYLOAD,
            "is_staff": True,
            "is_superuser": True,
            "role": "landlord",
            "organization": "other",
        },
        format="json",
    )
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data["token"]
    user = get_user_model().objects.get(email=PAYLOAD["email"])
    assert user.check_password(PAYLOAD["password"])
    assert not user.is_staff and not user.is_superuser
    assert not OrganizationMembership.objects.filter(user=user).exists()
    assert data["user"]["access"]["persona"] == "unassigned"
    client.credentials(HTTP_AUTHORIZATION="Token " + data["token"])
    assert client.get("/api/v1/organizations/onboarding/").json()["response_data"]["needs_setup"]


def test_registration_switch_keeps_signups_closed(settings):
    settings.BETA_REGISTRATION_OPEN = False
    client = APIClient()
    assert client.get(URL).json()["response_data"] == {"open": False}
    assert client.post(URL, PAYLOAD, format="json").status_code == 403
    assert not get_user_model().objects.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("password", "1234567890"),
        ("password", "short"),
        ("email", "not-email"),
        ("email", "user@mailinator.com"),
        ("first_name", " "),
        ("last_name", "x" * 151),
    ],
)
def test_registration_validates_input(field, value):
    response = APIClient().post(URL, {**PAYLOAD, field: value}, format="json")
    assert response.status_code == 400
    assert not get_user_model().objects.exists()


def test_existing_email_is_case_insensitive_and_does_not_issue_token():
    user = get_user_model().objects.create_user(
        username="existing", email="MOSES@example.com", password="OriginalPassphrase27!"
    )
    response = APIClient().post(URL, PAYLOAD, format="json")
    assert response.status_code == 400
    assert "token" not in response.json()["response_data"]
    user.refresh_from_db()
    assert user.check_password("OriginalPassphrase27!")
    assert get_user_model().objects.count() == 1


def test_registration_is_rate_limited():
    client = APIClient()
    for _ in range(5):
        assert client.post(URL, {}, format="json").status_code == 400
    assert client.post(URL, PAYLOAD, format="json").status_code == 429


def test_availability_checks_do_not_consume_registration_attempts():
    client = APIClient()
    for _ in range(8):
        assert client.get(URL).status_code == 200
    assert client.post(URL, PAYLOAD, format="json").status_code == 200
