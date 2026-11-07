"""Privileged accounts must enroll a confirmed authenticator before operating."""

from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from .models import TwoFactorDevice


def required(user):
    return bool(settings.REQUIRE_ADMIN_MFA and (user.is_staff or user.is_superuser))


def enrollment_required(user):
    return (
        required(user)
        and not TwoFactorDevice.objects.filter(
            user=user,
            is_confirmed=True,
        ).exists()
    )


def require_enrollment(request, user):
    if not enrollment_required(user):
        return
    path = request.path_info.rstrip("/")
    if (request.method == "GET" and path == "/api/v1/accounts/me") or (
        request.method == "POST"
        and path
        in {
            "/api/v1/accounts/2fa/setup",
            "/api/v1/accounts/2fa/verify",
            "/api/v1/accounts/logout",
            "/api/v1/accounts/email-verification",
            "/api/v1/accounts/email-verification/confirm",
        }
    ):
        return
    raise PermissionDenied("Set up two-factor authentication in Settings → Security first.")
