from rest_framework import serializers

from apps.common.serializers import OrganizationScopedSerializer
from apps.subscriptions.catalog import Resource
from apps.subscriptions.services import capacity_guard

from .models import Property, Unit


class PropertySerializer(OrganizationScopedSerializer):
    def create(self, validated_data):
        with capacity_guard(validated_data["organization"], Resource.PROPERTIES):
            return super().create(validated_data)

    units_count = serializers.IntegerField(read_only=True)
    occupied_units = serializers.IntegerField(read_only=True)
    vacant_units = serializers.IntegerField(read_only=True)
    maintenance_units = serializers.IntegerField(read_only=True)
    reserved_units = serializers.IntegerField(read_only=True)
    monthly_rent = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    occupied_rent = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    def validate_cover_image(self, value):
        if value is None:
            return value
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Cover photo must be 5MB or smaller.")
        if value.image.format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError("Choose a JPEG, PNG, or WebP photo.")
        if value.image.width * value.image.height > 25_000_000:
            raise serializers.ValidationError("Cover photo must be no larger than 25 megapixels.")
        return value

    class Meta:
        model = Property
        fields = [
            "id",
            "organization_id",
            "name",
            "property_type",
            "management_status",
            "address",
            "town",
            "province",
            "description",
            "cover_image",
            "units_count",
            "occupied_units",
            "vacant_units",
            "maintenance_units",
            "reserved_units",
            "monthly_rent",
            "occupied_rent",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]


class UnitSerializer(OrganizationScopedSerializer):
    def create(self, validated_data):
        with capacity_guard(validated_data["organization"], Resource.UNITS):
            return super().create(validated_data)

    property = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Property.objects.none()
    )
    property_name = serializers.CharField(source="property.name", read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        view = self.context.get("view")
        if view is not None:
            fields["property"].queryset = Property.objects.for_organization(view.get_organization())
        return fields

    class Meta:
        model = Unit
        fields = [
            "id",
            "organization_id",
            "property",
            "property_name",
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
