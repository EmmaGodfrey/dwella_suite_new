import re
from decimal import Decimal, InvalidOperation

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
    floor_area = AmountField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01"), required=False, allow_null=True
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
        ("floor_area", False, "65"),
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
        self.properties = {
            item.name.strip().casefold(): item
            for item in Property.objects.for_organization(organization).filter(is_active=True)
        }

    def key(self, data):
        return data["property"].pk, data["unit"].casefold()

    def existing(self, data):
        if Unit.objects.filter(property=data["property"], name__iexact=data["unit"]).exists():
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
            floor_area=data.get("floor_area"),
            notes=data["notes"],
        )


class TenantRow(serializers.Serializer):
    full_name = serializers.CharField(max_length=180)
    phone_number = serializers.CharField(max_length=40)
    email = serializers.EmailField(required=False, default="")
    national_id = serializers.CharField(max_length=40, required=False, default="")
    tpin = serializers.RegexField(
        r"^\d{10}$",
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

    def existing(self, data):
        # Archived tenants count: the phone number stays unique in the workspace.
        if Tenant.objects.filter(
            organization=self.organization, phone_number=data["phone_number"]
        ).exists():
            return "A tenant with this phone number is already on file."
        return None

    def label(self, data):
        return data["full_name"]

    def create(self, data):
        # Imported tenants start as applicants; a lease makes them active.
        return Tenant.objects.create(organization=self.organization, **data)
