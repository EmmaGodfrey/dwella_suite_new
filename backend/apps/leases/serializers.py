from decimal import Decimal

from rest_framework import serializers

from apps.common.serializers import OrganizationScopedSerializer
from apps.properties.models import Unit
from apps.tenants.models import Tenant

from .models import Lease
from .services import RENEWAL_TERMS, UNIT_TAKEN_MESSAGE, conflicting_leases, create_lease


def scoped_queryset(serializer, model):
    view = serializer.context.get("view")
    if view is None:
        return model.objects.none()
    return model.objects.for_organization(view.get_organization())


class LeaseSerializer(OrganizationScopedSerializer):
    tenant = serializers.SlugRelatedField(slug_field="public_id", queryset=Tenant.objects.none())
    unit = serializers.SlugRelatedField(slug_field="public_id", queryset=Unit.objects.none())
    monthly_rent = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    tenant_name = serializers.CharField(source="tenant.full_name", read_only=True)
    unit_name = serializers.CharField(source="unit.name", read_only=True)
    property_id = serializers.UUIDField(source="unit.property.public_id", read_only=True)
    property_name = serializers.CharField(source="unit.property.name", read_only=True)
    # Create-only switch: start the lease straight away instead of as a draft.
    activate = serializers.BooleanField(write_only=True, required=False, default=False)
    renewal_of_id = serializers.UUIDField(
        source="renewal_of.public_id", read_only=True, default=None
    )
    renewal_of_reference = serializers.CharField(
        source="renewal_of.reference", read_only=True, default=None
    )
    renewal = serializers.SerializerMethodField()

    class Meta:
        model = Lease
        fields = [
            "id",
            "organization_id",
            "reference",
            "tenant",
            "tenant_name",
            "unit",
            "unit_name",
            "property_id",
            "property_name",
            "start_date",
            "end_date",
            "monthly_rent",
            "deposit_amount",
            "rent_due_day",
            "late_fee_percent",
            "late_fee_grace_days",
            "notice_period_months",
            "status",
            "activated_at",
            "ended_at",
            "notes",
            "activate",
            "renewal_of_id",
            "renewal_of_reference",
            "renewal",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reference", "status", "activated_at", "ended_at", "is_active"]

    def get_fields(self):
        fields = super().get_fields()
        if "tenant" in fields:
            fields["tenant"].queryset = scoped_queryset(self, Tenant)
        fields["unit"].queryset = scoped_queryset(self, Unit).select_related("property")
        return fields

    def get_renewal(self, obj):
        # The renewal in progress or running, if any; ended ones are history.
        renewal = next(
            (item for item in obj.renewals.all() if item.status in Lease.OPEN_STATUSES), None
        )
        if renewal is None:
            return None
        return {
            "id": str(renewal.public_id),
            "reference": renewal.reference,
            "status": renewal.status,
            "start_date": renewal.start_date,
            "end_date": renewal.end_date,
        }

    def validate_rent_due_day(self, value):
        if not 1 <= value <= 28:
            raise serializers.ValidationError(
                "Choose a day from 1 to 28 so it exists in every month."
            )
        return value

    def validate_late_fee_percent(self, value):
        if not Decimal("0") <= value <= Decimal("100"):
            raise serializers.ValidationError("Late fee must be between 0 and 100 percent.")
        return value

    def validate_notice_period_months(self, value):
        if value > 12:
            raise serializers.ValidationError("Notice period cannot be more than 12 months.")
        return value

    def validate_deposit_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Deposit cannot be negative.")
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.renewal_of_id:
            # A renewal follows its lease: same tenant and unit, from the next day.
            fixed = {"tenant", "unit", "start_date"} & set(attrs)
            changed = [name for name in fixed if attrs[name] != getattr(instance, name)]
            if changed:
                raise serializers.ValidationError(
                    {name: ["A renewal keeps the tenant, unit and start date."] for name in changed}
                )
        if instance and instance.status != Lease.Status.DRAFT:
            locked = {"tenant", "unit", "start_date", "monthly_rent"} & set(attrs)
            changed = [name for name in locked if attrs[name] != getattr(instance, name)]
            if changed:
                raise serializers.ValidationError(
                    {
                        name: ["Cannot change this once the lease has left draft."]
                        for name in changed
                    }
                )

        unit = attrs.get("unit") or (instance.unit if instance else None)
        start = attrs.get("start_date") or (instance.start_date if instance else None)
        end = attrs.get("end_date") or (instance.end_date if instance else None)
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_date": ["End date must be after the start date."]}
            )

        if "monthly_rent" not in attrs and instance is None and unit is not None:
            attrs["monthly_rent"] = unit.rent_amount
        rent = attrs.get("monthly_rent")
        if rent is not None and rent <= 0:
            raise serializers.ValidationError({"monthly_rent": ["Rent must be more than zero."]})

        if unit is not None:
            if conflicting_leases(unit, instance).exists():
                raise serializers.ValidationError({"unit": [UNIT_TAKEN_MESSAGE]})
        return attrs

    def create(self, validated_data):
        return create_lease(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("activate", None)
        return super().update(instance, validated_data)


class RenewLeaseSerializer(serializers.ModelSerializer):
    """New end date and any changed terms; everything else copies over."""

    class Meta:
        model = Lease
        fields = ["end_date", *RENEWAL_TERMS]
        extra_kwargs = {name: {"required": False} for name in RENEWAL_TERMS}
        extra_kwargs["end_date"] = {"required": True}

    validate_rent_due_day = LeaseSerializer.validate_rent_due_day
    validate_late_fee_percent = LeaseSerializer.validate_late_fee_percent
    validate_notice_period_months = LeaseSerializer.validate_notice_period_months
    validate_deposit_amount = LeaseSerializer.validate_deposit_amount

    def validate_monthly_rent(self, value):
        if value <= 0:
            raise serializers.ValidationError("Rent must be more than zero.")
        return value


class TenantLeaseSerializer(LeaseSerializer):
    """Lease terms captured alongside a new tenant; the tenant is implied."""

    tenant = None

    class Meta(LeaseSerializer.Meta):
        fields = [name for name in LeaseSerializer.Meta.fields if name != "tenant"]


class LeaseSummarySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    unit_id = serializers.UUIDField(source="unit.public_id", read_only=True)
    unit_name = serializers.CharField(source="unit.name", read_only=True)
    property_name = serializers.CharField(source="unit.property.name", read_only=True)

    class Meta:
        model = Lease
        fields = [
            "id",
            "reference",
            "unit_id",
            "unit_name",
            "property_name",
            "start_date",
            "end_date",
            "monthly_rent",
            "deposit_amount",
            "status",
        ]
        read_only_fields = fields
