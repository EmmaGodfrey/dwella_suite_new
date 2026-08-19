from apps.common.serializers import OrganizationScopedSerializer

from .models import Property, PropertyOwner, Unit


class PropertyOwnerSerializer(OrganizationScopedSerializer):
    class Meta:
        model = PropertyOwner
        fields = [
            "id",
            "organization_id",
            "full_name",
            "email",
            "phone_number",
            "address",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]


class PropertySerializer(OrganizationScopedSerializer):
    class Meta:
        model = Property
        fields = [
            "id",
            "organization_id",
            "owner",
            "name",
            "property_type",
            "management_status",
            "address",
            "town",
            "province",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]


class UnitSerializer(OrganizationScopedSerializer):
    class Meta:
        model = Unit
        fields = [
            "id",
            "organization_id",
            "property",
            "name",
            "bedrooms",
            "bathrooms",
            "floor_area",
            "rent_amount",
            "occupancy_status",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]
