"""Production administrator enrollment and native-admin boundaries."""

import time

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, RequestFactory
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.common.middleware import NativeAdminBoundaryMiddleware

from .models import TwoFactorDevice
from .security import _hotp

pytestmark = pytest.mark.django_db
SECRET = "JBSWY3DPEHPK3PXP"


@pytest.fixture(autouse=True)
def policy(settings):
    settings.REQUIRE_ADMIN_MFA = True
    settings.NATIVE_ADMIN_ENABLED = False
    cache.clear()


@pytest.fixture
def admin():
    return get_user_model().objects.create_user(
        username="mfa-admin",
        email="mfa-admin@example.com",
        password="Synthetic-password-42",
        is_staff=True,
        is_superuser=True,
    )


def api_for(user):
    api = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api


def test_unenrolled_admin_token_is_limited_to_enrollment_and_logout(admin):
    api = api_for(admin)
    me = api.get("/api/v1/accounts/me/")
    assert me.status_code == 200 and me.json()["response_data"]["admin_mfa_required"]
    assert api.get("/api/v1/platform/users/").status_code == 403
    assert api.patch("/api/v1/accounts/me/", {"first_name": "changed"}).status_code == 403
    assert api.post("/api/v1/accounts/2fa/setup/").status_code == 200
    assert api.post("/api/v1/accounts/logout/").status_code == 200


def test_confirming_admin_authenticator_revokes_password_only_token(admin):
    api = api_for(admin)
    TwoFactorDevice.objects.create(user=admin, secret=SECRET)
    response = api.post(
        "/api/v1/accounts/2fa/verify/",
        {
            "code": _hotp(SECRET, int(time.time() // 30)),
        },
    )
    assert response.status_code == 200, response.content
    assert not Token.objects.filter(user=admin).exists()
    assert api.get("/api/v1/accounts/me/").status_code in {401, 403}
    login = APIClient().post(
        "/api/v1/accounts/login/",
        {
            "email": admin.email,
            "password": "Synthetic-password-42",
        },
    )
    assert login.status_code == 200
    assert login.json()["response_data"]["two_factor_required"]
    assert "token" not in login.json()["response_data"]


def test_bad_authenticator_code_never_unlocks_admin_and_cannot_disable_required_mfa(admin):
    api = api_for(admin)
    device = TwoFactorDevice.objects.create(user=admin, secret=SECRET)
    assert api.post("/api/v1/accounts/2fa/verify/", {"code": "wrong!"}).status_code == 400
    assert api.get("/api/v1/platform/users/").status_code == 403
    device.mark_confirmed()
    assert (
        api.post(
            "/api/v1/accounts/2fa/disable/",
            {
                "password": "Synthetic-password-42",
                "code": _hotp(SECRET, int(time.time() // 30)),
            },
        ).status_code
        == 403
    )
    assert TwoFactorDevice.objects.get().is_confirmed


def test_normal_personal_account_does_not_require_admin_enrollment():
    user = get_user_model().objects.create_user(username="ordinary", email="ordinary@example.com")
    response = api_for(user).get("/api/v1/accounts/me/")
    assert response.status_code == 200
    assert not response.json()["response_data"]["admin_mfa_required"]


@pytest.mark.parametrize("path", ["/admin", "/admin/", "/admin/login/", "/admin/auth/user/"])
def test_native_admin_is_closed_without_exposing_login(path):
    assert Client().get(path).status_code == 404


def test_native_boundary_does_not_block_spa_or_api_admin_routes():
    sentinel = object()
    middleware = NativeAdminBoundaryMiddleware(lambda request: sentinel)
    assert middleware(RequestFactory().get("/api/v1/platform/users/")) is sentinel
    assert middleware(RequestFactory().get("/administrator/")) is sentinel
