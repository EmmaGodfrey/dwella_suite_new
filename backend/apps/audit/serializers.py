from rest_framework import serializers

from apps.organizations.models import Organization

from .models import SupportSession


class SupportSessionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    organization = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Organization.objects.all()
    )
    organization_name = serializers.CharField(source="organization.__str__", read_only=True)
    reason = serializers.CharField(min_length=5, max_length=300, trim_whitespace=True)

    class Meta:
        model = SupportSession
        fields = [
            "id",
            "organization",
            "organization_name",
            "reason",
            "started_at",
            "ended_at",
            "expires_at",
        ]
        read_only_fields = ["started_at", "ended_at", "expires_at"]

    def validate_organization(self, organization):
        if not organization.is_active:
            raise serializers.ValidationError("This workspace is suspended.")
        return organization
