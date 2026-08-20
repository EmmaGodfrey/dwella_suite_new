import time

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.signing import TimestampSigner
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import IdentityVerification, PasswordResetRequest, TwoFactorDevice, UserProfile
from .security import _hotp

User = get_user_model()

TINY_GIF = (
    b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00"
    b"\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture
def user(db):
    user = User.objects.create_user(
        username="admin@example.com",
        email="admin@example.com",
        password="StrongerPass123",
        first_name="Dwella",
    )
    return user


@pytest.mark.django_db
def test_login_happy_path_returns_token_and_user(user):
    client = APIClient()

    response = client.post(
        "/api/v1/accounts/login/",
        {"email": "ADMIN@example.com", "password": "StrongerPass123"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["token"]
    assert response.data["user"]["email"] == "admin@example.com"
    assert response.data["user"]["has_two_factor"] is False

    payload = response.json()
    assert payload["success"] is True
    assert payload["response_code"] == 200
    assert payload["response_message"] == "Operation completed successfully"
    assert payload["response_data"]["token"] == response.data["token"]


@pytest.mark.django_db
def test_login_rejects_bad_password(user):
    client = APIClient()

    response = client.post(
        "/api/v1/accounts/login/",
        {"email": user.email, "password": "wrong"},
        format="json",
    )

    assert response.status_code == 400
    assert "Invalid email or password" in str(response.data)

    payload = response.json()
    assert payload["success"] is False
    assert payload["response_code"] == 400
    assert "Invalid email or password" in payload["response_message"]
    assert "response_data" in payload


@pytest.mark.django_db
def test_login_rate_limit_blocks_repeated_attempts(user):
    client = APIClient()
    payload = {"email": user.email, "password": "wrong"}

    for _ in range(8):
        assert client.post("/api/v1/accounts/login/", payload, format="json").status_code == 400
    assert client.post("/api/v1/accounts/login/", payload, format="json").status_code == 429


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_URL="https://app.dwella.test",
)
def test_password_reset_request_sends_generic_response_and_email(user):
    client = APIClient()

    response = client.post(
        "/api/v1/accounts/password-reset/",
        {"email": user.email},
        format="json",
    )

    assert response.status_code == 202
    assert "If that email exists" in response.data["detail"]
    assert PasswordResetRequest.objects.filter(email=user.email).exists()
    assert len(mail.outbox) == 1
    assert "https://app.dwella.test/login?reset_uid=" in mail.outbox[0].body


@pytest.mark.django_db
def test_password_reset_blocks_disposable_email():
    client = APIClient()

    response = client.post(
        "/api/v1/accounts/password-reset/",
        {"email": "person@mailinator.com"},
        format="json",
    )

    assert response.status_code == 400
    assert "permanent email" in str(response.data)


@pytest.mark.django_db
@override_settings(
    AUTH_PASSWORD_VALIDATORS=[
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {"min_length": 10},
        },
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]
)
def test_password_reset_confirm_rejects_weak_password(user):
    client = APIClient()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    response = client.post(
        "/api/v1/accounts/password-reset/confirm/",
        {"uid": uid, "token": token, "password": "123"},
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_password_reset_confirm_updates_password_and_revokes_tokens(user):
    Token.objects.create(user=user)
    client = APIClient()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    response = client.post(
        "/api/v1/accounts/password-reset/confirm/",
        {"uid": uid, "token": token, "password": "NewStrongPass123"},
        format="json",
    )

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.check_password("NewStrongPass123")
    assert not Token.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_current_user_requires_authentication():
    response = APIClient().get("/api/v1/accounts/me/")

    assert response.status_code == 403
    assert response.json()["response_code"] == 403


@pytest.mark.django_db
def test_profile_update_changes_user_and_profile(user):
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        "/api/v1/accounts/me/",
        {
            "first_name": "Emmanuel",
            "last_name": "Godfrey",
            "phone_number": "+260 977 000 111",
            "job_title": "Property Manager",
        },
        format="json",
    )

    user.refresh_from_db()
    profile = UserProfile.objects.get(user=user)
    assert response.status_code == 200
    assert user.first_name == "Emmanuel"
    assert profile.phone_number == "+260 977 000 111"
    assert response.json()["response_data"]["profile"]["job_title"] == "Property Manager"


@pytest.mark.django_db
def test_profile_update_rejects_invalid_phone(user):
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        "/api/v1/accounts/me/",
        {"phone_number": "call me maybe"},
        format="json",
    )

    assert response.status_code == 400
    assert "valid phone number" in response.json()["response_message"]


@pytest.mark.django_db
def test_avatar_upload_updates_current_user_profile(user):
    client = APIClient()
    client.force_authenticate(user=user)
    avatar = SimpleUploadedFile("avatar.gif", TINY_GIF, content_type="image/gif")

    response = client.post("/api/v1/accounts/me/avatar/", {"avatar": avatar}, format="multipart")

    profile = UserProfile.objects.get(user=user)
    assert response.status_code == 200
    assert profile.avatar
    assert response.json()["response_data"]["profile"]["avatar_url"]


@pytest.mark.django_db
def test_avatar_upload_requires_authentication():
    avatar = SimpleUploadedFile("avatar.gif", TINY_GIF, content_type="image/gif")
    response = APIClient().post(
        "/api/v1/accounts/me/avatar/",
        {"avatar": avatar},
        format="multipart",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_identity_verification_submit_sets_pending_status(user):
    client = APIClient()
    client.force_authenticate(user=user)
    document = SimpleUploadedFile("document.gif", TINY_GIF, content_type="image/gif")

    response = client.post(
        "/api/v1/accounts/me/verification/",
        {
            "legal_name": "Emmanuel Godfrey",
            "document_type": "nrc",
            "document_number": "123456789",
            "document_image": document,
        },
        format="multipart",
    )

    verification = IdentityVerification.objects.get(user=user)
    assert response.status_code == 200
    assert verification.status == IdentityVerification.Status.PENDING
    assert verification.document_number_last4 == "6789"
    assert response.json()["response_data"]["identity_verification"]["has_document"] is True


@pytest.mark.django_db
def test_identity_verification_rejects_duplicate_pending_submission(user):
    IdentityVerification.objects.create(user=user, status=IdentityVerification.Status.PENDING)
    client = APIClient()
    client.force_authenticate(user=user)
    document = SimpleUploadedFile("document.gif", TINY_GIF, content_type="image/gif")

    response = client.post(
        "/api/v1/accounts/me/verification/",
        {
            "legal_name": "Emmanuel Godfrey",
            "document_type": "nrc",
            "document_number": "123456789",
            "document_image": document,
        },
        format="multipart",
    )

    assert response.status_code == 400
    assert "already submitted" in response.json()["response_message"]


@pytest.mark.django_db
def test_security_headers_are_sent():
    response = APIClient().get("/api/health/")

    assert response.status_code == 200
    assert response.json()["response_data"]["status"] == "ok"
    assert response["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response["Content-Security-Policy"]
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_two_factor_setup_and_login_challenge(user):
    client = APIClient()
    client.force_authenticate(user=user)

    setup_response = client.post("/api/v1/accounts/2fa/setup/", {}, format="json")
    assert setup_response.status_code == 200
    secret = setup_response.data["secret"]
    code = _hotp(secret, int(time.time() // 30))

    verify_response = client.post("/api/v1/accounts/2fa/verify/", {"code": code}, format="json")
    assert verify_response.status_code == 200
    assert TwoFactorDevice.objects.get(user=user).is_confirmed

    client.force_authenticate(user=None)
    login_response = client.post(
        "/api/v1/accounts/login/",
        {"email": user.email, "password": "StrongerPass123"},
        format="json",
    )
    assert login_response.status_code == 200
    assert login_response.data["two_factor_required"] is True
    assert "token" not in login_response.data

    challenge_response = client.post(
        "/api/v1/accounts/login/2fa/",
        {"challenge_token": login_response.data["challenge_token"], "code": code},
        format="json",
    )
    assert challenge_response.status_code == 200
    assert challenge_response.data["token"]


@pytest.mark.django_db
def test_two_factor_login_rejects_bad_code(user):
    TwoFactorDevice.objects.create(user=user, secret="JBSWY3DPEHPK3PXP", is_confirmed=True)
    challenge = TimestampSigner(salt="accounts.two_factor.challenge").sign(str(user.pk))
    client = APIClient()

    response = client.post(
        "/api/v1/accounts/login/2fa/",
        {"challenge_token": challenge, "code": "000000"},
        format="json",
    )

    assert response.status_code == 400
    assert "Invalid authentication code" in response.data["detail"]
