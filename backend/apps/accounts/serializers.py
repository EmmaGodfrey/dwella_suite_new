from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from apps.organizations.serializers import OrganizationMembershipSerializer

from .models import IdentityVerification, UserProfile
from .security import is_disposable_email, normalize_email, verify_totp

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["phone_number", "job_title", "avatar_url", "updated_at"]
        read_only_fields = ["avatar_url", "updated_at"]

    def get_avatar_url(self, obj):
        if not obj.avatar:
            return ""
        request = self.context.get("request")
        url = obj.avatar.url
        return request.build_absolute_uri(url) if request else url


class IdentityVerificationSerializer(serializers.ModelSerializer):
    has_document = serializers.SerializerMethodField()

    class Meta:
        model = IdentityVerification
        fields = [
            "status",
            "legal_name",
            "document_type",
            "document_number_last4",
            "has_document",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "status",
            "legal_name",
            "document_type",
            "document_number_last4",
            "has_document",
            "rejection_reason",
            "submitted_at",
            "reviewed_at",
        ]

    def get_has_document(self, obj):
        return bool(obj.document_image)


class CurrentUserSerializer(serializers.ModelSerializer):
    has_two_factor = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    identity_verification = serializers.SerializerMethodField()
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
            "profile",
            "identity_verification",
            "memberships",
        ]
        read_only_fields = ["id", "is_staff", "is_active", "profile", "memberships"]

    def get_has_two_factor(self, obj):
        return hasattr(obj, "two_factor_device") and obj.two_factor_device.is_confirmed

    def get_profile(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return UserProfileSerializer(profile, context=self.context).data

    def get_identity_verification(self, obj):
        verification, _ = IdentityVerification.objects.get_or_create(user=obj)
        return IdentityVerificationSerializer(verification, context=self.context).data


class CurrentUserUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=32, allow_blank=True, required=False)
    job_title = serializers.CharField(max_length=120, allow_blank=True, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number", "job_title"]
        extra_kwargs = {
            "first_name": {"required": False, "allow_blank": False, "max_length": 150},
            "last_name": {"required": False, "allow_blank": False, "max_length": 150},
        }

    def validate_phone_number(self, value):
        cleaned = value.strip()
        if cleaned and not cleaned.replace("+", "", 1).replace(" ", "").isdigit():
            raise serializers.ValidationError("Enter a valid phone number.")
        return cleaned

    def update(self, instance, validated_data):
        profile_data = {
            key: validated_data.pop(key)
            for key in ["phone_number", "job_title"]
            if key in validated_data
        }
        for attr, value in validated_data.items():
            setattr(instance, attr, value.strip() if isinstance(value, str) else value)
        if validated_data:
            instance.save(update_fields=list(validated_data.keys()))

        if profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value.strip() if isinstance(value, str) else value)
            profile.save(update_fields=[*profile_data.keys(), "updated_at"])
        return instance


class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField()

    def validate_avatar(self, value):
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Profile picture must be 2MB or smaller.")
        return value


class IdentityVerificationSubmitSerializer(serializers.Serializer):
    legal_name = serializers.CharField(max_length=150)
    document_type = serializers.ChoiceField(choices=IdentityVerification.DocumentType.choices)
    document_number = serializers.CharField(max_length=64, write_only=True)
    document_image = serializers.ImageField()

    def validate_legal_name(self, value):
        value = " ".join(value.split())
        if len(value.split()) < 2:
            raise serializers.ValidationError("Enter your full legal name.")
        return value

    def validate_document_number(self, value):
        cleaned = value.strip().replace(" ", "")
        if len(cleaned) < 4:
            raise serializers.ValidationError("Document number is too short.")
        return cleaned

    def validate_document_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Verification document must be 5MB or smaller.")
        return value


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
