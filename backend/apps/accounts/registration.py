from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .security import is_disposable_email, normalize_email
from .views import issue_auth_response

User = get_user_model()
UNAVAILABLE = (
    "Unable to create an account with these details. Try signing in or resetting your password."
)


class RegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate_email(self, value):
        value = normalize_email(value)
        if is_disposable_email(value):
            raise serializers.ValidationError("Use a permanent email address.")
        return value

    def validate(self, attrs):
        candidate = User(
            username=attrs["email"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "registration"

    def get_throttles(self):
        # Availability checks on sign-in must not consume account creation attempts.
        self.throttle_scope = "registration" if self.request.method == "POST" else None
        return super().get_throttles()

    def get(self, request):
        return Response({"open": settings.BETA_REGISTRATION_OPEN})

    def post(self, request):
        if not settings.BETA_REGISTRATION_OPEN:
            return Response(
                {"detail": "Registration is not open yet. Beta opens 18 November 2026."}, status=403
            )
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(email__iexact=data["email"]).exists():
            return Response({"detail": UNAVAILABLE}, status=400)
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=data["email"], **data)
                from .access_state import require_new_account_verification

                require_new_account_verification(user)
        except IntegrityError:
            return Response({"detail": UNAVAILABLE}, status=400)
        response = issue_auth_response(user, request)
        from .email_verification import send_verification

        response.data["verification_delivery"] = send_verification(request, user)
        return response
