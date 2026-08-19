from rest_framework import serializers

from apps.common.serializers import PublicIdModelSerializer

from .models import Organization, OrganizationMembership


class OrganizationSerializer(PublicIdModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "display_name",
            "logo",
            "email",
            "phone_number",
            "address",
            "town",
            "country",
            "currency",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrganizationMembershipSerializer(PublicIdModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "organization",
            "user_email",
            "user_name",
            "role",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "user_email", "user_name", "created_at"]
