from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PasswordResetRequest, TwoFactorDevice
from .security import (
    frontend_reset_url,
    get_client_ip,
    make_totp_secret,
    throttle_by_key,
    totp_uri,
    verify_totp,
)
from .serializers import (
    CurrentUserSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    TwoFactorChallengeSerializer,
    TwoFactorSetupVerifySerializer,
)

User = get_user_model()
signer = TimestampSigner(salt="accounts.two_factor.challenge")


def issue_auth_response(user, request):
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {
            "token": token.key,
            "user": CurrentUserSerializer(user, context={"request": request}).data,
        }
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
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

    def post(self, request):
        device, _ = TwoFactorDevice.objects.update_or_create(
            user=request.user,
            defaults={"secret": make_totp_secret(), "is_confirmed": False, "confirmed_at": None},
        )
        return Response(
            {
                "secret": device.secret,
                "provisioning_uri": totp_uri(device.secret, request.user.email),
            }
        )


class TwoFactorSetupVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "two_factor"

    def post(self, request):
        device = getattr(request.user, "two_factor_device", None)
        if not device:
            return Response(
                {"detail": "Start 2FA setup before verifying a code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TwoFactorSetupVerifySerializer(data=request.data, context={"device": device})
        serializer.is_valid(raise_exception=True)
        device.mark_confirmed()
        return Response({"enabled": True})


class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        TwoFactorDevice.objects.filter(user=request.user).delete()
        return Response({"enabled": False})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)


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
            send_mail(
                "Reset your Dwella Suite password",
                f"Use this link to reset your password: {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

        return Response(
            {"detail": "If that email exists, a password reset link has been sent."},
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        return Response({"detail": "Password reset complete."})
