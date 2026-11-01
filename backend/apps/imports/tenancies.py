"""Preview and atomically import units, tenants and draft leases together."""

from decimal import Decimal

from django.db.models.functions import Lower
from rest_framework import serializers

from apps.leases.models import Lease
from apps.leases.services import next_lease_reference
from apps.properties.models import Unit
from apps.subscriptions.catalog import Resource
from apps.tenants.details import missing_details
from apps.tenants.models import Tenant

from .importers import AmountField, TenantImporter, TenantRow, UnitImporter


class LeaseRow(serializers.Serializer):
    lease_start = serializers.DateField()
    lease_end = serializers.DateField()
    monthly_rent = AmountField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    deposit_amount = AmountField(max_digits=12, decimal_places=2, min_value=Decimal("0"), default=0)
    rent_due_day = serializers.IntegerField(min_value=1, max_value=28, default=1)

    def validate(self, attrs):
        if attrs["lease_end"] <= attrs["lease_start"]:
            raise serializers.ValidationError({"lease_end": "The lease must end after it starts."})
        return attrs


class TenancyImporter(UnitImporter):
    kind = "tenancies"
    noun = "portfolio"
    columns = (
        *UnitImporter.columns,
        *((key, False, example) for key, _, example in TenantImporter.columns if key != "notes"),
        ("lease_start", False, "2026-11-01"),
        ("lease_end", False, "2027-10-31"),
        ("monthly_rent", False, "3500"),
        ("deposit_amount", False, "3500"),
        ("rent_due_day", False, "5"),
    )
    aliases = {
        **UnitImporter.aliases,
        **TenantImporter.aliases,
        "name": "unit",
        "start_date": "lease_start",
        "end_date": "lease_end",
        "monthly_rent": "monthly_rent",
    }

    def clean(self, values):
        unit, errors = super().clean(values)
        if errors:
            return None, errors
        tenant_keys = set(TenantRow().fields) - {"notes"}
        occupied = any(values.get(key) for key in tenant_keys)
        if not occupied:
            if any(values.get(key) for key in LeaseRow().fields):
                return None, {
                    "full_name": ["Add a tenant for these lease terms, or clear the lease columns."]
                }
            return {**unit, "tenant_data": None, "lease_data": None}, None
        tenant = TenantRow(data={key: value for key, value in values.items() if key in tenant_keys})
        lease = LeaseRow(
            data={**values, "monthly_rent": values.get("monthly_rent", values.get("rent_amount"))}
        )
        tenant.is_valid()
        lease.is_valid()
        errors = {**tenant.errors, **lease.errors}
        if errors:
            return None, {key: [str(v) for v in value] for key, value in errors.items()}
        return {
            **unit,
            "tenant_data": tenant.validated_data,
            "lease_data": lease.validated_data,
        }, None

    def prime(self, rows):
        self.ambiguous_units = set()
        self.units = {}
        # A case-sensitive database may already contain both "A" and "a".
        # Never choose one silently when matching case-insensitive sheet labels.
        for unit in (
            Unit.objects.for_organization(self.organization)
            .filter(property__in={row["property"].pk for row in rows})
            .annotate(lookup=Lower("name"))
            .filter(lookup__in={row["unit"].lower() for row in rows})
        ):
            key = (unit.property_id, unit.name.casefold())
            if key in self.units:
                self.ambiguous_units.add(key)
            self.units[key] = unit
        self.busy = set(
            Lease.objects.filter(
                unit__in=self.units.values(), status__in=Lease.OPEN_STATUSES
            ).values_list("unit_id", flat=True)
        )
        self.tenants = {
            item.phone_number: item
            for item in Tenant.objects.filter(
                organization=self.organization,
                phone_number__in={
                    row["tenant_data"]["phone_number"] for row in rows if row["tenant_data"]
                },
            )
        }
        self.conflicts = set()
        seen = {}
        for row in rows:
            tenant = row["tenant_data"]
            if tenant:
                phone = tenant["phone_number"]
                if phone in seen and seen[phone] != tenant:
                    self.conflicts.add(phone)
                seen[phone] = tenant

    def existing(self, data):
        if self.key(data) in self.ambiguous_units:
            return "More than one unit matches this label. Review the unit names first."
        unit = self.units.get(self.key(data))
        if unit and (
            not unit.is_active or unit.pk in self.busy or unit.occupancy_status != "vacant"
        ):
            return (
                "This unit is archived, unavailable or already has an open lease. Review it first."
            )
        tenant_data = data["tenant_data"]
        if not tenant_data:
            return "This vacant unit is already on file." if unit else None
        if tenant_data["phone_number"] in self.conflicts:
            return (
                "This phone has conflicting tenant details in the file. Use one consistent record."
            )
        tenant = self.tenants.get(tenant_data["phone_number"])
        if tenant:
            keys = ["full_name", "national_id", "tpin", "tenant_type", "company_registration"]
            if not tenant.is_active or any(
                tenant_data.get(key)
                and getattr(tenant, key)
                and str(tenant_data[key]).casefold() != str(getattr(tenant, key)).casefold()
                for key in keys
            ):
                return (
                    "This phone matches an archived or different tenant. Review the tenant first."
                )
        return None

    def label(self, data):
        tenant = data["tenant_data"]
        suffix = tenant["full_name"] if tenant else "Vacant"
        unit_state = "existing unit" if self.key(data) in self.units else "new unit"
        tenant_state = (
            "existing tenant" if tenant and tenant["phone_number"] in self.tenants else "new tenant"
        )
        action = f"{unit_state}, {tenant_state}; draft lease" if tenant else f"{unit_state}; vacant"
        return f"{super().label(data)} · {suffix} ({action})"

    def capacities(self, results):
        rows = [item["data"] for item in results]
        phones = {row["tenant_data"]["phone_number"] for row in rows if row["tenant_data"]}
        return [
            (Resource.UNITS, sum(self.key(row) not in self.units for row in rows)),
            (Resource.TENANTS, len(phones - self.tenants.keys())),
        ]

    def match_signature(self, data):
        unit = self.units.get(self.key(data))
        tenant = data["tenant_data"]
        tenant = self.tenants.get(tenant["phone_number"]) if tenant else None
        return [
            [str(unit.public_id), unit.updated_at.isoformat()] if unit else None,
            [str(tenant.public_id), tenant.updated_at.isoformat()] if tenant else None,
        ]

    def create_many(self, results):
        rows = [item["data"] for item in results]
        new_units = [row for row in rows if self.key(row) not in self.units]
        inserted = Unit.objects.bulk_create(
            [
                Unit(
                    organization=self.organization,
                    property=row["property"],
                    name=row["unit"],
                    rent_amount=row["rent_amount"],
                    bedrooms=row["bedrooms"],
                    bathrooms=row["bathrooms"],
                    notes=row["notes"],
                )
                for row in new_units
            ],
            batch_size=100,
        )
        self.units.update(
            {self.key(row): unit for row, unit in zip(new_units, inserted, strict=True)}
        )
        new_tenants = {
            row["tenant_data"]["phone_number"]: row["tenant_data"]
            for row in rows
            if row["tenant_data"] and row["tenant_data"]["phone_number"] not in self.tenants
        }
        tenants = Tenant.objects.bulk_create(
            [Tenant(organization=self.organization, **data) for data in new_tenants.values()],
            batch_size=100,
        )
        self.tenants.update({item.phone_number: item for item in tenants})
        occupied = [row for row in rows if row["tenant_data"]]
        first = int(next_lease_reference(self.organization).split("-")[-1]) if occupied else 0
        leases = []
        for index, row in enumerate(occupied):
            terms = row["lease_data"]
            leases.append(
                Lease(
                    organization=self.organization,
                    reference=f"LSE-{first + index:04d}",
                    unit=self.units[self.key(row)],
                    tenant=self.tenants[row["tenant_data"]["phone_number"]],
                    start_date=terms["lease_start"],
                    end_date=terms["lease_end"],
                    monthly_rent=terms["monthly_rent"],
                    deposit_amount=terms["deposit_amount"],
                    rent_due_day=terms["rent_due_day"],
                    status=Lease.Status.DRAFT,
                )
            )
        Lease.objects.bulk_create(leases, batch_size=100)
        return [self.units[self.key(row)] for row in rows]

    def row_missing_details(self, data):
        tenant = data["tenant_data"]
        return missing_details(self.tenants.get(tenant["phone_number"], tenant)) if tenant else []
