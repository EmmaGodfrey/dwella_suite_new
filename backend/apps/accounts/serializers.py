from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from apps.organizations.serializers import OrganizationMembershipSerializer

from .security import is_disposable_email, normalize_email, verify_totp

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    has_two_factor = serializers.SerializerMethodField()
    memberships = OrganizationMembershipSerializer(
        source="organization_memberships",
        many=True,
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "has_two_factor",
            "memberships",
        ]
        read_only_fields = ["id", "is_staff", "is_active", "memberships"]

    def get_has_two_factor(self, obj):
        return hasattr(obj, "two_factor_device") and obj.two_factor_device.is_confirmed


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower()
        password = attrs["password"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid email or password.") from exc

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.get_username(),
            password=password,
        )

        if authenticated_user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not authenticated_user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        attrs["user"] = authenticated_user
        return attrs


class TwoFactorChallengeSerializer(serializers.Serializer):
    challenge_token = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)


class TwoFactorSetupVerifySerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value):
        device = self.context["device"]
        if not verify_totp(device.secret, value):
            raise serializers.ValidationError("Invalid authentication code.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        email = normalize_email(value)
        if is_disposable_email(email):
            raise serializers.ValidationError("Please use a permanent email address.")
        return email


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise serializers.ValidationError("Invalid password reset link.") from exc

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Invalid or expired password reset link.")

        attrs["user"] = user
        return attrs
