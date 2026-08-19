from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.organizations.serializers import OrganizationMembershipSerializer

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
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
            "memberships",
        ]
        read_only_fields = ["id", "is_staff", "is_active", "memberships"]
