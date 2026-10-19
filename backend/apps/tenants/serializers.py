from django.db import transaction
from rest_framework import serializers

from apps.common.serializers import OrganizationScopedSerializer
from apps.leases.models import Lease
from apps.leases.serializers import LeaseSummarySerializer, TenantLeaseSerializer
from apps.leases.services import create_lease

from .models import Tenant
from .phone import normalize_phone_number

# The lease a tenant row shows: the live one first, then one still being set up.
LEASE_PRIORITY = {Lease.Status.ACTIVE: 0, Lease.Status.PENDING_SIGNATURE: 1, Lease.Status.DRAFT: 2}


class TenantSerializer(OrganizationScopedSerializer):
    current_lease = serializers.SerializerMethodField()
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, default=0)
    lease = TenantLeaseSerializer(write_only=True, required=False)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "organization_id",
            "full_name",
            "phone_number",
            "email",
            "national_id",
            "status",
            "notes",
            "current_lease",
            "balance",
            "lease",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "is_active"]

    def validate_full_name(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Enter the tenant's full name.")
        return value

    def validate_phone_number(self, value):
        normalized = normalize_phone_number(value)
        if normalized is None:
            raise serializers.ValidationError(
                "Enter a valid phone number, for example 097 123 4567."
            )
        view = self.context.get("view")
        organization = view.get_organization() if view else None
        duplicates = Tenant.objects.for_organization(organization).filter(phone_number=normalized)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("Another tenant already uses this phone number.")
        return normalized

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        if self.instance and "lease" in attrs:
            raise serializers.ValidationError(
                {"lease": ["Add a lease from the Leases page for an existing tenant."]}
            )
        return attrs

    def get_current_lease(self, obj):
        leases = [lease for lease in obj.leases.all() if lease.status in LEASE_PRIORITY]
        if not leases:
            return None
        lease = min(
            leases, key=lambda item: (LEASE_PRIORITY[item.status], -item.start_date.toordinal())
        )
        return LeaseSummarySerializer(lease).data

    @transaction.atomic
    def create(self, validated_data):
        lease_data = validated_data.pop("lease", None)
        tenant = super().create(validated_data)
        if lease_data:
            create_lease(organization=tenant.organization, tenant=tenant, **lease_data)
            tenant.refresh_from_db()
        return tenant
