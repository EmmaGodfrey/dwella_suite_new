from decimal import Decimal

from rest_framework import serializers

from apps.common.serializers import OrganizationScopedSerializer
from apps.leases.models import Lease
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import MaintenancePhoto, MaintenanceRequest, MaintenanceUpdate, Vendor
from .services import create_request

MAX_PHOTOS = 8


def scoped(serializer, model):
    view = serializer.context.get("view")
    if view is None:
        return model.objects.none()
    return model.objects.for_organization(view.get_organization())


def display_name(user):
    return (user.get_full_name() or user.username) if user else None


class VendorSerializer(OrganizationScopedSerializer):
    open_jobs = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Vendor
        fields = [
            "id",
            "organization_id",
            "name",
            "trade",
            "contact_name",
            "phone_number",
            "email",
            "notes",
            "open_jobs",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["is_active"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Enter the vendor's name.")
        duplicates = scoped(self, Vendor).filter(name__iexact=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("You already have a vendor with this name.")
        return value


class MaintenanceUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceUpdate
        fields = ["id", "kind", "body", "is_internal", "author_name", "created_at"]
        read_only_fields = ["kind", "author_name", "created_at"]

    def get_author_name(self, obj):
        return display_name(obj.author)

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Write a message first.")
        if len(value) > 2000:
            raise serializers.ValidationError("Keep messages under 2,000 characters.")
        return value


class MaintenancePhotoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = MaintenancePhoto
        fields = ["id", "image", "created_at"]
        read_only_fields = ["created_at"]

    def validate_image(self, value):
        if value.size > 8 * 1024 * 1024:
            raise serializers.ValidationError("Photos must be 8MB or smaller.")
        if value.image.format not in {"JPEG", "PNG", "WEBP"}:
            raise serializers.ValidationError("Choose a JPEG, PNG, or WebP photo.")
        if value.image.width * value.image.height > 40_000_000:
            raise serializers.ValidationError("Photos must be no larger than 40 megapixels.")
        return value


class MaintenanceRequestSerializer(OrganizationScopedSerializer):
    property = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Property.objects.none()
    )
    unit = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Unit.objects.none(), required=False, allow_null=True
    )
    tenant = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Tenant.objects.none(), required=False, allow_null=True
    )
    property_name = serializers.CharField(source="property.name", read_only=True)
    unit_name = serializers.CharField(source="unit.name", read_only=True, default=None)
    tenant_name = serializers.CharField(source="tenant.full_name", read_only=True, default=None)
    vendor_id = serializers.UUIDField(source="vendor.public_id", read_only=True, default=None)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True, default=None)
    invoice_id = serializers.UUIDField(source="invoice.public_id", read_only=True, default=None)
    invoice_reference = serializers.CharField(
        source="invoice.reference", read_only=True, default=None
    )
    reported_by_name = serializers.SerializerMethodField()
    photos_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "organization_id",
            "reference",
            "title",
            "description",
            "property",
            "property_name",
            "unit",
            "unit_name",
            "tenant",
            "tenant_name",
            "category",
            "priority",
            "status",
            "source",
            "access_notes",
            "permission_to_enter",
            "vendor_id",
            "vendor_name",
            "scheduled_for",
            "estimated_cost",
            "actual_cost",
            "charge_to_tenant",
            "invoice_id",
            "invoice_reference",
            "reported_by_name",
            "photos_count",
            "started_at",
            "completed_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "reference",
            "status",
            "scheduled_for",
            "estimated_cost",
            "actual_cost",
            "charge_to_tenant",
            "started_at",
            "completed_at",
            "cancelled_at",
        ]

    def get_fields(self):
        fields = super().get_fields()
        fields["property"].queryset = scoped(self, Property)
        fields["unit"].queryset = scoped(self, Unit)
        fields["tenant"].queryset = scoped(self, Tenant)
        if self.instance is not None:
            # Where the job is stays fixed once it is logged.
            fields["property"].read_only = True
            fields["source"].read_only = True
        return fields

    def get_reported_by_name(self, obj):
        return display_name(obj.reported_by)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Say what needs fixing.")
        return value

    def validate(self, attrs):
        prop = attrs.get("property") or getattr(self.instance, "property", None)
        unit = attrs.get("unit", getattr(self.instance, "unit", None))
        if unit and unit.property_id != prop.id:
            raise serializers.ValidationError({"unit": ["This unit is in another property."]})
        if self.instance is None and unit and "tenant" not in attrs:
            # Default the reporter to whoever lives there now.
            lease = Lease.objects.filter(unit=unit, status=Lease.Status.ACTIVE).first()
            attrs["tenant"] = lease.tenant if lease else None
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return create_request(reported_by=request.user, **validated_data)


class MaintenanceRequestDetailSerializer(MaintenanceRequestSerializer):
    updates = MaintenanceUpdateSerializer(many=True, read_only=True)
    photos = MaintenancePhotoSerializer(many=True, read_only=True)

    class Meta(MaintenanceRequestSerializer.Meta):
        fields = [*MaintenanceRequestSerializer.Meta.fields, "updates", "photos"]


class AssignSerializer(serializers.Serializer):
    vendor = serializers.SlugRelatedField(slug_field="public_id", queryset=Vendor.objects.none())
    scheduled_for = serializers.DateTimeField(required=False, allow_null=True)
    estimated_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0")
    )
    charge_to_tenant = serializers.BooleanField(required=False)

    def get_fields(self):
        fields = super().get_fields()
        fields["vendor"].queryset = scoped(self, Vendor).filter(is_active=True)
        return fields


class CompleteSerializer(serializers.Serializer):
    actual_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0")
    )


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")
