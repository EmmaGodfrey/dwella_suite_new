import re

from rest_framework import serializers

from apps.accounts.security import is_disposable_email, normalize_email

from .models import BetaApplication

PHONE_PATTERN = re.compile(r"^\+?[\d\s-]{9,16}$")
VALID_ROLES = {"Landlord", "Agent", "Property manager"}


class BetaApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetaApplication
        fields = ["name", "phone", "email", "role", "units", "town"]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
            "town": {"required": False, "allow_blank": True},
        }

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Enter your name.")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not PHONE_PATTERN.fullmatch(value):
            raise serializers.ValidationError("Enter a valid phone number.")
        return value

    def validate_email(self, value):
        if not value:
            return ""
        value = normalize_email(value)
        if is_disposable_email(value):
            raise serializers.ValidationError("Use a permanent email address.")
        return value

    def validate_role(self, value):
        if value not in VALID_ROLES:
            raise serializers.ValidationError("Choose a valid role.")
        return value


class BetaApplicationAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetaApplication
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "role",
            "units",
            "town",
            "status",
            "internal_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "name",
            "phone",
            "email",
            "role",
            "units",
            "town",
            "created_at",
            "updated_at",
        ]
