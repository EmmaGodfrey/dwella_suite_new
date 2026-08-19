from rest_framework import serializers


class PublicIdModelSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)


class OrganizationScopedSerializer(PublicIdModelSerializer):
    organization_id = serializers.UUIDField(source="organization.public_id", read_only=True)
