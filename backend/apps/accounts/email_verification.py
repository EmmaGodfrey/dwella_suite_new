import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, Throttled, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.audit.services import record_event

from .access_state import email_status, mark_email_verified
from .account_mail import send_account_mail
from .models import EmailVerificationLink
from .security import normalize_email

INVALID = "This verification link has expired or is unavailable. Sign in to request a new one."


def secret_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


@transaction.atomic
def send_verification(request, user):
    user = get_user_model().objects.select_for_update().get(pk=user.pk)
    if not user.is_active:
        raise PermissionDenied("This account is unavailable.")
    if email_status(user)["verified"]:
        return {"verified": True, "sent": False}
    email = normalize_email(user.email)
    if not email:
        raise ValidationError("Add a permanent email address before requesting verification.")
    previous = EmailVerificationLink.objects.filter(user=user).order_by("-created_at").first()
    if previous and previous.created_at > timezone.now() - timedelta(seconds=60):
        raise Throttled(wait=60, detail="Wait a minute before requesting another email.")
    token = secrets.token_urlsafe(32)
    link = EmailVerificationLink.objects.create(
        user=user,
        email=email,
        token_hash=secret_hash(token),
        expires_at=timezone.now() + timedelta(hours=24),
    )
    url = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
    delivered = send_account_mail(
        "Confirm your Dwella email address",
        f"Confirm your email address:\n\n{url}\n\nThis link expires in 24 hours. "
        "Confirming does not sign you in. If you did not request this, ignore this email.",
        email,
    )
    if not delivered:
        link.delete()
        return {"verified": False, "sent": False}
    EmailVerificationLink.objects.filter(
        user=user, used_at__isnull=True, revoked_at__isnull=True
    ).exclude(pk=link.pk).update(revoked_at=timezone.now())
    record_event(request, "account.verification_sent", user)
    return {"verified": False, "sent": True}


@transaction.atomic
def confirm_verification(request, token):
    candidate = EmailVerificationLink.objects.filter(token_hash=secret_hash(token)).first()
    if not candidate:
        raise ValidationError(INVALID)
    user = get_user_model().objects.select_for_update().get(pk=candidate.user_id)
    link = EmailVerificationLink.objects.select_for_update().get(pk=candidate.pk)
    if (
        not user.is_active
        or link.used_at
        or link.revoked_at
        or link.expires_at <= timezone.now()
        or link.email != normalize_email(user.email)
    ):
        raise ValidationError(INVALID)
    mark_email_verified(user)
    link.used_at = timezone.now()
    link.save(update_fields=["used_at", "updated_at"])
    record_event(request, "account.email_verified", user)
    return {"verified": True, "sign_in_required": True}


class VerificationTokenSerializer(serializers.Serializer):
    token = serializers.RegexField(r"^[A-Za-z0-9_-]{32,100}$")


class VerificationUserThrottle(UserRateThrottle):
    scope = "email_verification_user"
    rate = "5/hour"


class VerificationPublicThrottle(AnonRateThrottle):
    scope = "email_verification_ip"
    rate = "20/hour"


class NoStoreAccountView(APIView):
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        response["Referrer-Policy"] = "no-referrer"
        return response


class EmailVerificationView(NoStoreAccountView):
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        return (
            [*super().get_throttles(), VerificationUserThrottle()]
            if self.request.method == "POST"
            else super().get_throttles()
        )

    def get(self, request):
        return Response({**email_status(request.user), "email": request.user.email})

    def post(self, request):
        data = send_verification(request, request.user)
        return Response(data, status=200 if data["sent"] or data["verified"] else 503)


class EmailVerificationConfirmView(NoStoreAccountView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [VerificationPublicThrottle]

    def post(self, request):
        data = VerificationTokenSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(confirm_verification(request, data.validated_data["token"]))
