from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from apps.accounts.access_state import email_status_from_state
from apps.accounts.security import is_disposable_email, normalize_email
from apps.accounts.serializers import (
    CurrentUserSerializer,
    IdentityVerificationSerializer,
    UserProfileSerializer,
)
from apps.common.permissions import access_representation
from apps.organizations.models import Organization, OrganizationMembership

User = get_user_model()


class PlatformUserSerializer(CurrentUserSerializer):
    class Meta(CurrentUserSerializer.Meta):
        fields = CurrentUserSerializer.Meta.fields + ["last_login", "date_joined"]
        read_only_fields = fields

    def get_access(self, obj):
        memberships = sorted(
            (m for m in obj.organization_memberships.all() if m.is_active),
            key=lambda m: m.created_at,
        )
        return access_representation(
            obj,
            membership=memberships[0] if memberships else None,
            verified_access=not self.get_email_verification(obj)["required"],
        )

    def get_email_verification(self, obj):
        return email_status_from_state(obj, getattr(obj, "account_access_state", None))

    def get_profile(self, obj):
        return (
            UserProfileSerializer(obj.profile, context=self.context).data
            if hasattr(obj, "profile")
            else {"phone_number": ""}
        )

    def get_identity_verification(self, obj):
        return (
            IdentityVerificationSerializer(obj.identity_verification).data
            if hasattr(obj, "identity_verification")
            else {"status": "not_submitted"}
        )


class UserFilters(serializers.Serializer):
    active = serializers.BooleanField(required=False)
    staff = serializers.BooleanField(required=False)
    two_factor = serializers.BooleanField(required=False)
    workspace = serializers.UUIDField(required=False)
    role = serializers.ChoiceField(choices=OrganizationMembership.Role.choices, required=False)
    persona = serializers.ChoiceField(
        choices=["platform_admin", "landlord", "tenant", "unassigned"],
        required=False,
    )
    identity_status = serializers.ChoiceField(
        choices=["pending", "approved", "rejected", "not_submitted"],
        required=False,
    )


class UserProfileInput(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=150)
    phone_number = serializers.RegexField(r"^\+?[\d\s-]{7,32}$", allow_blank=True, required=False)

    def validate_email(self, value):
        value = normalize_email(value)
        if is_disposable_email(value):
            raise serializers.ValidationError("Use a permanent email address.")
        users = User.objects.filter(Q(email__iexact=value) | Q(username__iexact=value))
        if self.instance:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value


class CreateUserInput(UserProfileInput):
    account_type = serializers.ChoiceField(choices=["landlord", "member", "platform_admin"])
    workspace_name = serializers.CharField(max_length=180, required=False)
    organization = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=Organization.objects.filter(is_active=True),
        required=False,
    )
    role = serializers.ChoiceField(choices=OrganizationMembership.Role.choices, required=False)

    def validate(self, data):
        if data["account_type"] == "landlord" and not data.get("workspace_name"):
            raise serializers.ValidationError({"workspace_name": "Enter a workspace name."})
        if data["account_type"] == "member":
            if not data.get("organization"):
                raise serializers.ValidationError({"organization": "Choose an active workspace."})
            if not data.get("role"):
                raise serializers.ValidationError({"role": "Choose a workspace role."})
        return data


class MembershipInput(serializers.Serializer):
    organization = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=Organization.objects.filter(is_active=True),
    )
    role = serializers.ChoiceField(choices=OrganizationMembership.Role.choices)
    remove = serializers.BooleanField(default=False)
