import re
from decimal import Decimal, InvalidOperation

from django.db.models.functions import Lower, Trim
from rest_framework import serializers

from apps.properties.models import Property, Unit
from apps.subscriptions.catalog import Resource
from apps.tenants.models import Tenant
from apps.tenants.phone import normalize_phone_number

from .services import Importer


class AmountField(serializers.DecimalField):
    """Accepts spreadsheet money such as "K 3,500" or "3500.00"."""

    def to_internal_value(self, data):
        text = re.sub(r"[\s,]|^(zmw|k)", "", str(data).strip().lower())
        try:
            Decimal(text)
        except InvalidOperation:
            self.fail("invalid")
        return super().to_internal_value(text)


class UnitRow(serializers.Serializer):
    property = serializers.CharField(max_length=180)
    unit = serializers.CharField(max_length=80)
    rent_amount = AmountField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    bedrooms = serializers.IntegerField(min_value=0, max_value=50, required=False, default=0)
    bathrooms = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        min_value=Decimal("0"),
        max_value=Decimal("50"),
        required=False,
        default=0,
    )
    notes = serializers.CharField(max_length=2000, required=False, default="")

    def validate_property(self, value):
        found = self.context["importer"].properties.get(value.casefold())
        if found is None:
            raise serializers.ValidationError(
                f'No property is called "{value}". Add it first or fix the name.'
            )
        return found


class UnitImporter(Importer):
    kind = "units"
    resource = Resource.UNITS
    noun = "unit"
    columns = (
        ("property", True, "Mutendere Court"),
        ("unit", True, "2A"),
        ("rent_amount", True, "3500"),
        ("bedrooms", False, "2"),
        ("bathrooms", False, "1"),
        ("notes", False, "Ground floor"),
    )
    aliases = {
        "property_name": "property",
        "unit_name": "unit",
        "name": "unit",
        "rent": "rent_amount",
        "monthly_rent": "rent_amount",
        "beds": "bedrooms",
        "baths": "bathrooms",
    }
    row_serializer = UnitRow

    def __init__(self, organization):
        super().__init__(organization)
        self.properties = {}

    def prepare(self, rows):
        names = {row.get("property", "").strip().lower() for row in rows}
        for item in (
            Property.objects.for_organization(self.organization)
            .filter(is_active=True)
            .annotate(lookup=Lower(Trim("name")))
            .filter(lookup__in=names)
        ):
            key = item.name.strip().casefold()
            self.properties[key] = None if key in self.properties else item

    def key(self, data):
        return data["property"].pk, data["unit"].casefold()

    def prime(self, rows):
        names = (
            Unit.objects.filter(property__in={row["property"] for row in rows})
            .annotate(lookup=Lower("name"))
            .filter(lookup__in={row["unit"].lower() for row in rows})
        )
        self.known = {(pk, name.casefold()) for pk, name in names.values_list("property", "name")}

    def existing(self, data):
        if self.key(data) in self.known:
            return f"{data['property'].name} already has a unit called {data['unit']}."
        return None

    def label(self, data):
        return f"{data['property'].name} · {data['unit']}"

    def create(self, data):
        return Unit.objects.create(
            organization=self.organization,
            property=data["property"],
            name=data["unit"],
            rent_amount=data["rent_amount"],
            bedrooms=data["bedrooms"],
            bathrooms=data["bathrooms"],
            notes=data["notes"],
        )

    def create_many(self, results):
        return Unit.objects.bulk_create(
            [
                Unit(
                    organization=self.organization,
                    property=item["data"]["property"],
                    name=item["data"]["unit"],
                    rent_amount=item["data"]["rent_amount"],
                    bedrooms=item["data"]["bedrooms"],
                    bathrooms=item["data"]["bathrooms"],
                    notes=item["data"]["notes"],
                )
                for item in results
            ],
            batch_size=100,
        )


class TenantRow(serializers.Serializer):
    tenant_type = serializers.ChoiceField(choices=Tenant.TenantType.choices, default="individual")
    identity_type = serializers.ChoiceField(choices=Tenant.IdentityType.choices, default="nrc")
    identity_country = serializers.RegexField(r"^[A-Za-z]{2}$", default="ZM")
    billing_address = serializers.CharField(max_length=1000, required=False, default="")
    company_registration = serializers.CharField(max_length=80, required=False, default="")
    representative_name = serializers.CharField(max_length=180, required=False, default="")
    representative_phone = serializers.CharField(max_length=40, required=False, default="")
    full_name = serializers.CharField(max_length=180)
    phone_number = serializers.CharField(max_length=40)
    email = serializers.EmailField(required=False, default="")
    national_id = serializers.CharField(max_length=40, required=False, default="")
    tpin = serializers.RegexField(
        r"^[0-9]{10}$",
        required=False,
        default="",
        error_messages={"invalid": "A TPIN is 10 digits."},
    )
    notes = serializers.CharField(max_length=2000, required=False, default="")

    def validate_full_name(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Enter the tenant's full name.")
        return value

    def validate_phone_number(self, value):
        phone = normalize_phone_number(value)
        if phone is None:
            raise serializers.ValidationError(
                "Enter a valid phone number, for example 097 123 4567."
            )
        return phone

    def validate_email(self, value):
        return value.strip().lower()

    def validate_identity_country(self, value):
        return value.upper()

    def validate_representative_phone(self, value):
        if not value:
            return ""
        return self.validate_phone_number(value)


class TenantImporter(Importer):
    kind = "tenants"
    resource = Resource.TENANTS
    noun = "tenant"
    columns = (
        ("full_name", True, "Mwila Banda"),
        ("phone_number", True, "0971234567"),
        ("email", False, "mwila@example.com"),
        ("national_id", False, "123456/10/1"),
        ("tpin", False, ""),
        ("notes", False, ""),
        ("tenant_type", False, "individual"),
        ("identity_type", False, "nrc"),
        ("identity_country", False, "ZM"),
        ("billing_address", False, "Plot 1, Lusaka"),
        ("company_registration", False, ""),
        ("representative_name", False, ""),
        ("representative_phone", False, ""),
    )
    aliases = {
        "name": "full_name",
        "tenant": "full_name",
        "tenant_name": "full_name",
        "phone": "phone_number",
        "mobile": "phone_number",
        "nrc": "national_id",
        "email_address": "email",
    }
    row_serializer = TenantRow

    def key(self, data):
        return data["phone_number"]

    def prime(self, rows):
        # Archived tenants count: the phone number stays unique in the workspace.
        self.known = set(
            Tenant.objects.filter(
                organization=self.organization,
                phone_number__in={row["phone_number"] for row in rows},
            ).values_list("phone_number", flat=True)
        )

    def existing(self, data):
        if data["phone_number"] in self.known:
            return "A tenant with this phone number is already on file."
        return None

    def label(self, data):
        return data["full_name"]

    def row_missing_details(self, data):
        from apps.tenants.details import missing_details

        return missing_details(data)

    def create(self, data):
        # Imported tenants start as applicants; a lease makes them active.
        return Tenant.objects.create(organization=self.organization, **data)

    def create_many(self, results):
        return Tenant.objects.bulk_create(
            [Tenant(organization=self.organization, **item["data"]) for item in results],
            batch_size=100,
        )
