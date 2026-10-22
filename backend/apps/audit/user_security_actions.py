from smtplib import SMTPException

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

from apps.accounts.models import TwoFactorDevice

from .services import record_event
from .user_actions import revoke_access
from .user_services import lock_target, send_access_email


class DeliveryUnavailable(APIException):
    status_code = 503
    default_detail = "Email delivery failed. Please try again."


class UserSecurityActions:
    @action(detail=True, methods=["post"], url_path="password-reset")
    @transaction.atomic
    def password_reset(self, request, pk=None):
        user = self.get_object()
        if not user.is_active:
            raise ValidationError("Reactivate this account before sending a reset link.")
        try:
            send_access_email(user)
        except (SMTPException, OSError) as exc:
            raise DeliveryUnavailable() from exc
        record_event(request, "user.password_reset_sent", user)
        return Response({"sent": True})

    @action(detail=True, methods=["post"], url_path="sign-out")
    @transaction.atomic
    def sign_out(self, request, pk=None):
        user = lock_target(request, self.get_object().pk)
        revoke_access(request, user)
        record_event(request, "user.signed_out", user)
        return Response({"signed_out": True})

    @action(detail=True, methods=["post"], url_path="reset-2fa")
    @transaction.atomic
    def reset_two_factor(self, request, pk=None):
        user = lock_target(request, self.get_object().pk)
        TwoFactorDevice.objects.filter(user=user).delete()
        revoke_access(request, user)
        record_event(request, "user.two_factor_reset", user)
        return Response({"reset": True})
