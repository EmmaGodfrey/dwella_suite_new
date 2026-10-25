from django.contrib.auth import get_user_model
from django.contrib.auth import logout as session_logout
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_event

from .handy_agent import handy_agent_enabled, issue_handy_agent_token
from .models import IdentityVerification, PasswordResetRequest, TwoFactorDevice, UserProfile
from .security import (
    frontend_reset_url,
    get_client_ip,
    make_totp_secret,
    throttle_by_key,
    totp_uri,
    verify_totp,
)
from .serializers import (
    AvatarUploadSerializer,
    CurrentUserSerializer,
    CurrentUserUpdateSerializer,
    IdentityVerificationSubmitSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    TwoFactorChallengeSerializer,
    TwoFactorSetupVerifySerializer,
)

User = get_user_model()
signer = TimestampSigner(salt="accounts.two_factor.challenge")


class HandyAgentConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"enabled": handy_agent_enabled()})


class HandyAgentTokenView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "handy_agent_token"

    def post(self, request):
        token, expires_at = issue_handy_agent_token(request.user, request)
        return Response(
            {
                "token": token,
                "expires_at": expires_at.isoformat(),
                # Handy forwards this only after the user approves an action.
                # Reuse the short-lived, workspace-scoped JWT instead of
                # exposing Dwella's durable API token to a third party.
                "host_authorization": f"Bearer {token}",
            }
        )


@transaction.atomic
def issue_auth_response(user, request):
    token, _ = Token.objects.get_or_create(user=user)
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    request.user = user
    record_event(request, "account.signed_in", user)
    return Response(
        {
            "token": token.key,
            "user": CurrentUserSerializer(user, context={"request": request}).data,
        }
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
    # Credentials authenticate this public endpoint; a revoked browser token
    # must not prevent a new login. Password validation and throttling still apply.
    authentication_classes = []
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        device = getattr(user, "two_factor_device", None)

        if device and device.is_confirmed:
            challenge_token = signer.sign(str(user.pk))
            return Response(
                {
                    "two_factor_required": True,
                    "challenge_token": challenge_token,
                    "user": {
                        "email": user.email,
                    },
                }
            )

        return issue_auth_response(user, request)


class TwoFactorLoginVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "two_factor"

    def post(self, request):
        serializer = TwoFactorChallengeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        challenge_token = serializer.validated_data["challenge_token"]
        code = serializer.validated_data["code"]

        try:
            user_id = signer.unsign(challenge_token, max_age=300)
            user = User.objects.get(pk=user_id, is_active=True)
        except (BadSignature, SignatureExpired, User.DoesNotExist):
            return Response(
                {"detail": "Invalid or expired 2FA challenge."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = getattr(user, "two_factor_device", None)
        if not device or not device.is_confirmed or not verify_totp(device.secret, code):
            return Response(
                {"detail": "Invalid authentication code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return issue_auth_response(user, request)


class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "two_factor"

    @transaction.atomic
    def post(self, request):
        request.user = User.objects.select_for_update().get(pk=request.user.pk)
        if TwoFactorDevice.objects.filter(user=request.user, is_confirmed=True).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Two-factor authentication is already enabled.")
        device, _ = TwoFactorDevice.objects.update_or_create(
            user=request.user,
            defaults={"secret": make_totp_secret(), "is_confirmed": False, "confirmed_at": None},
        )
        record_event(request, "account.2fa_setup_started", request.user)
        return Response(
            {
                "secret": device.secret,
                "provisioning_uri": totp_uri(device.secret, request.user.email),
            }
        )


class TwoFactorSetupVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "two_factor"

    @transaction.atomic
    def post(self, request):
        request.user = User.objects.select_for_update().get(pk=request.user.pk)
        device = TwoFactorDevice.objects.select_for_update().filter(user=request.user).first()
        if not device:
            return Response(
                {"detail": "Start 2FA setup before verifying a code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TwoFactorSetupVerifySerializer(data=request.data, context={"device": device})
        serializer.is_valid(raise_exception=True)
        device.mark_confirmed()
        record_event(request, "account.2fa_enabled", request.user)
        return Response({"enabled": True})


class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "two_factor"

    @transaction.atomic
    def post(self, request):
        request.user = User.objects.select_for_update().get(pk=request.user.pk)
        from .access_security import TwoFactorRemovalSerializer

        data = TwoFactorRemovalSerializer(data=request.data, context={"request": request})
        data.is_valid(raise_exception=True)
        TwoFactorDevice.objects.filter(user=request.user).delete()
        record_event(request, "account.2fa_disabled", request.user)
        return Response({"enabled": False})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = CurrentUserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(CurrentUserSerializer(user, context={"request": request}).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        from apps.audit.models import SupportSession
        from apps.audit.services import record_event

        now = timezone.now()
        sessions = SupportSession.objects.select_for_update().filter(
            admin=request.user, ended_at__isnull=True
        )
        for support_session in sessions:
            support_session.ended_at = now
            support_session.save(update_fields=["ended_at", "updated_at"])
            record_event(
                request,
                "support_session.ended",
                support_session,
                organization=support_session.organization,
                support_session=str(support_session.public_id),
                reason=support_session.reason,
                cause="sign_out",
            )
        Token.objects.filter(user=request.user).delete()
        session_logout(request)
        request._request.support_event_recorded = True
        return Response({"signed_out": True})


class CurrentUserAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.avatar = serializer.validated_data["avatar"]
        profile.save(update_fields=["avatar", "updated_at"])
        return Response(CurrentUserSerializer(request.user, context={"request": request}).data)


class IdentityVerificationSubmitView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = IdentityVerificationSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_number = serializer.validated_data.pop("document_number")
        verification, _ = IdentityVerification.objects.get_or_create(user=request.user)
        if verification.status in [
            IdentityVerification.Status.PENDING,
            IdentityVerification.Status.APPROVED,
        ]:
            return Response(
                {"detail": "Identity verification is already submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        verification.status = IdentityVerification.Status.PENDING
        verification.legal_name = serializer.validated_data["legal_name"]
        verification.document_type = serializer.validated_data["document_type"]
        verification.document_number_last4 = document_number[-4:]
        verification.document_image = serializer.validated_data["document_image"]
        verification.rejection_reason = ""
        verification.submitted_at = timezone.now()
        verification.reviewed_at = None
        verification.save(
            update_fields=[
                "status",
                "legal_name",
                "document_type",
                "document_number_last4",
                "document_image",
                "rejection_reason",
                "submitted_at",
                "reviewed_at",
                "updated_at",
            ]
        )
        return Response(CurrentUserSerializer(request.user, context={"request": request}).data)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        ip_address = get_client_ip(request)
        throttle_by_key("password_reset_email", email, limit=3, timeout=60 * 60)

        PasswordResetRequest.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:255],
        )

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = frontend_reset_url(uid, token)
            from .account_mail import send_account_mail

            send_account_mail(
                "Reset your Dwella Suite password",
                f"Use this link to reset your password: {reset_url}",
                user.email,
            )

        return Response(
            {"detail": "If that email exists, a password reset link has been sent."},
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    @transaction.atomic
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.select_for_update().get(pk=serializer.validated_data["user"].pk)
        if not user.is_active or not default_token_generator.check_token(
            user, serializer.validated_data["token"]
        ):
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Invalid or expired password reset link.")
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        from .access_state import mark_email_verified

        mark_email_verified(user)
        Token.objects.filter(user=user).delete()
        return Response({"detail": "Password reset complete."})
