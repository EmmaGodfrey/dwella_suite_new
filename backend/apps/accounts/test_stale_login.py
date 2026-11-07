import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_login_uses_credentials_even_with_revoked_browser_token():
    user = get_user_model().objects.create_user(
        username="fresh@example.com", email="fresh@example.com", password="test-valid-password"
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token deleted-session")
    response = client.post(
        "/api/v1/accounts/login/",
        {"email": user.email, "password": "test-valid-password"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["response_data"]["user"]["id"] == user.pk
    assert response.json()["response_data"]["token"]
    assert client.get("/api/v1/accounts/me/").status_code in (401, 403)


@pytest.mark.parametrize(
    "data",
    [
        {"email": "fresh@example.com", "password": "wrong"},
        {"email": "unknown@example.com", "password": "wrong"},
        {"email": "malformed", "password": "wrong"},
        {},
    ],
)
def test_revoked_token_does_not_bypass_login_validation(data):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token deleted-session")
    assert client.post("/api/v1/accounts/login/", data, format="json").status_code == 400


def test_two_factor_still_requires_a_valid_challenge_with_revoked_token():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token deleted-session")
    assert (
        client.post(
            "/api/v1/accounts/login/2fa/",
            {"challenge_token": "invalid", "code": "123456"},
            format="json",
        ).status_code
        == 400
    )
