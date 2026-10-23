import re

from rest_framework import serializers

from apps.accounts.security import is_disposable_email, normalize_email

from .models import BetaApplication, BetaEmail

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


class BetaEmailSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = BetaEmail
        fields = ["kind", "label", "sent_at"]


class BetaApplicationAdminSerializer(BetaApplicationSerializer):
    emails = BetaEmailSerializer(many=True, read_only=True)
    account_email = serializers.EmailField(source="account.email", read_only=True, default=None)
    early_access = serializers.SerializerMethodField()

    def get_early_access(self, obj):
        from django.utils import timezone

        from .emails import beta_open_date

        return any(
            e.kind == "access" and timezone.localtime(e.sent_at).date() < beta_open_date()
            for e in obj.emails.all()
        )

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
            "source",
            "internal_notes",
            "unsubscribed_at",
            "emails",
            "early_access",
            "account_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "source",
            "unsubscribed_at",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
            "town": {"required": False, "allow_blank": True},
        }

    def validate_email(self, value):
        value = super().validate_email(value)
        if self.instance and self.instance.email and not value:
            raise serializers.ValidationError("An applicant's email can be changed, not removed.")
        if self.instance and self.instance.account_id and value != self.instance.email:
            raise serializers.ValidationError(
                "Their account already exists, so the email can no longer change here."
            )
        if value:
            others = BetaApplication.objects.filter(email__iexact=value)
            if self.instance:
                others = others.exclude(pk=self.instance.pk)
            if others.exists():
                raise serializers.ValidationError("This email has already signed up.")
        return value


class BetaApplicationAdminCreateSerializer(BetaApplicationAdminSerializer):
    """Someone signed up by the Dwella team, e.g. after a call. Email is required
    because the whole beta sequence is delivered by email."""

    send_welcome = serializers.BooleanField(write_only=True, default=True)
    give_early_access = serializers.BooleanField(write_only=True, default=False)

    class Meta(BetaApplicationAdminSerializer.Meta):
        fields = BetaApplicationAdminSerializer.Meta.fields + ["send_welcome", "give_early_access"]
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "town": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        validated_data.pop("send_welcome", None)
        validated_data.pop("give_early_access", None)
        validated_data["source"] = BetaApplication.Source.ADMIN
        return super().create(validated_data)
