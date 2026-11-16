"""Tenant-facing shapes.

These list fields explicitly rather than reusing the manager serializers, so a
field added for managers (notes, internal costs, identity numbers, who recorded
a payment) never reaches a tenant by accident.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.billing.models import Invoice, InvoiceLine, Payment
from apps.billing.receipt_fields import AllocationFields
from apps.common.serializers import PublicIdModelSerializer
from apps.documents.models import DocumentVersion, SignedLeaseOriginal
from apps.leases.models import Lease
from apps.maintenance.models import MaintenancePhoto, MaintenanceRequest, MaintenanceUpdate
from apps.maintenance.serializers import display_name
from apps.tenants.models import Tenant
from apps.tenants.phone import normalize_phone_number


def issuer(organization):
    return {
        "name": str(organization),
        "address": organization.address,
        "town": organization.town,
        "phone_number": organization.phone_number,
        "email": organization.email,
        "currency": organization.currency,
    }


class LeaseSerializer(PublicIdModelSerializer):
    property_name = serializers.CharField(source="unit.property.name", read_only=True)
    property_address = serializers.CharField(source="unit.property.address", read_only=True)
    unit_name = serializers.CharField(source="unit.name", read_only=True)

    class Meta:
        model = Lease
        fields = [
            "id",
            "reference",
            "status",
            "property_name",
            "property_address",
            "unit_name",
            "start_date",
            "end_date",
            "monthly_rent",
            "deposit_amount",
            "rent_due_day",
            "late_fee_percent",
            "late_fee_grace_days",
            "notice_period_months",
            "activated_at",
            "ended_at",
        ]
        read_only_fields = fields


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ["kind", "description", "amount"]
        read_only_fields = fields


class PaymentSerializer(PublicIdModelSerializer):
    invoice_id = serializers.UUIDField(source="invoice.public_id", read_only=True)
    invoice_reference = serializers.CharField(source="invoice.reference", read_only=True)
    reversed = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "receipt_number",
            "invoice_id",
            "invoice_reference",
            "amount",
            "method",
            "paid_on",
            "reference",
            "reversed",
            "reversed_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_reversed(self, obj):
        return obj.reversed_at is not None


class ReceiptSerializer(AllocationFields, PaymentSerializer):
    missing_details = serializers.SerializerMethodField()

    def get_missing_details(self, obj):
        from apps.tenants.details import receipt_missing_details

        return receipt_missing_details(obj)

    issuer = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source="tenant.full_name", read_only=True)
    property_name = serializers.CharField(source="invoice.unit.property.name", default=None)
    unit_name = serializers.CharField(source="invoice.unit.name", default=None)
    invoice_total = serializers.DecimalField(
        source="invoice.total", max_digits=12, decimal_places=2, read_only=True
    )
    current_balance = serializers.DecimalField(
        source="invoice.balance", max_digits=12, decimal_places=2, read_only=True
    )

    class Meta(PaymentSerializer.Meta):
        fields = [
            *PaymentSerializer.Meta.fields,
            "issuer",
            "missing_details",
            "tenant_name",
            "property_name",
            "unit_name",
            "invoice_total",
            "current_balance",
            "allocation",
            "deposit_held",
        ]
        read_only_fields = fields

    def get_issuer(self, obj):
        return issuer(obj.organization)


class InvoiceSerializer(PublicIdModelSerializer):
    lease_reference = serializers.CharField(source="lease.reference", read_only=True, default=None)
    property_name = serializers.CharField(source="unit.property.name", read_only=True, default=None)
    unit_name = serializers.CharField(source="unit.name", read_only=True, default=None)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    days_overdue = serializers.SerializerMethodField()
    lines = InvoiceLineSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "reference",
            "lease_reference",
            "property_name",
            "unit_name",
            "period_start",
            "issue_date",
            "due_date",
            "total",
            "amount_paid",
            "balance",
            "status",
            "days_overdue",
            "is_opening_balance",
            "lines",
            "created_at",
        ]
        read_only_fields = fields

    def get_days_overdue(self, obj):
        if obj.status not in Invoice.UNPAID_STATUSES:
            return 0
        return max(0, (timezone.localdate() - obj.due_date).days)


class InvoiceDetailSerializer(InvoiceSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    issuer = serializers.SerializerMethodField()

    class Meta(InvoiceSerializer.Meta):
        fields = [*InvoiceSerializer.Meta.fields, "payments", "issuer"]
        read_only_fields = fields

    def get_issuer(self, obj):
        return issuer(obj.organization)


class SignatureSerializer(serializers.Serializer):
    role = serializers.CharField()
    signer_name = serializers.CharField()
    signed_at = serializers.DateTimeField()


class DocumentSerializer(PublicIdModelSerializer):
    lease_id = serializers.UUIDField(source="lease.public_id", read_only=True)
    signatures = SignatureSerializer(many=True, read_only=True)
    awaiting_your_signature = serializers.SerializerMethodField()

    class Meta:
        model = DocumentVersion
        fields = [
            "id",
            "lease_id",
            "version",
            "status",
            "page_count",
            "sha256",
            "signatures",
            "awaiting_your_signature",
            "created_at",
        ]
        read_only_fields = fields

    def get_awaiting_your_signature(self, obj):
        # Signing itself stays on the emailed, code-verified link.
        return obj.status == DocumentVersion.Status.SIGNING and not any(
            signature.role == "tenant" for signature in obj.signatures.all()
        )


class OriginalSerializer(PublicIdModelSerializer):
    lease_id = serializers.UUIDField(source="lease.public_id", read_only=True)

    class Meta:
        model = SignedLeaseOriginal
        fields = ["id", "lease_id", "filename", "page_count", "sha256", "created_at"]
        read_only_fields = fields


class MaintenanceUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    author_name = serializers.SerializerMethodField()
    from_you = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceUpdate
        fields = ["id", "kind", "body", "author_name", "from_you", "created_at"]
        read_only_fields = ["kind", "author_name", "from_you", "created_at"]

    def get_author_name(self, obj):
        return display_name(obj.author)

    def get_from_you(self, obj):
        request = self.context.get("request")
        return bool(request and obj.author_id == request.user.pk)

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
        read_only_fields = fields


class MaintenanceSerializer(PublicIdModelSerializer):
    lease = serializers.UUIDField(write_only=True, required=False)
    property_name = serializers.CharField(source="property.name", read_only=True)
    unit_name = serializers.CharField(source="unit.name", read_only=True, default=None)
    vendor_name = serializers.CharField(source="vendor.name", read_only=True, default=None)
    charge_invoice_id = serializers.SerializerMethodField()
    reported_by_you = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "reference",
            "lease",
            "title",
            "description",
            "category",
            "priority",
            "status",
            "property_name",
            "unit_name",
            "permission_to_enter",
            "access_notes",
            "vendor_name",
            "scheduled_for",
            "charge_invoice_id",
            "reported_by_you",
            "started_at",
            "completed_at",
            "cancelled_at",
            "created_at",
        ]
        read_only_fields = [
            "reference",
            "status",
            "vendor_name",
            "scheduled_for",
            "charge_invoice_id",
            "started_at",
            "completed_at",
            "cancelled_at",
        ]

    def get_charge_invoice_id(self, obj):
        # Only invoices addressed to this tenant; the portal scope already ensures it.
        return str(obj.invoice.public_id) if obj.charge_to_tenant and obj.invoice_id else None

    def get_reported_by_you(self, obj):
        request = self.context.get("request")
        return bool(request and obj.reported_by_id == request.user.pk)

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Say briefly what needs fixing.")
        return value


class MaintenanceDetailSerializer(MaintenanceSerializer):
    updates = serializers.SerializerMethodField()
    photos = MaintenancePhotoSerializer(many=True, read_only=True)

    class Meta(MaintenanceSerializer.Meta):
        fields = [*MaintenanceSerializer.Meta.fields, "updates", "photos"]

    def get_updates(self, obj):
        # Internal notes stay with the manager's team.
        visible = [update for update in obj.updates.all() if not update.is_internal]
        return MaintenanceUpdateSerializer(visible, many=True, context=self.context).data


class ProfileSerializer(PublicIdModelSerializer):
    """The tenant's own contact and document details.

    TPIN and billing address change over time, so tenants may always edit
    them. Identity and company details are filled in by the tenant only while
    blank; once recorded, the property manager owns corrections.
    """

    # Fields a tenant may set only while they are empty.
    FILL_ONCE = (
        "national_id",
        "identity_type",
        "identity_country",
        "company_registration",
        "representative_name",
        "representative_phone",
    )

    phone_number = serializers.CharField(max_length=40)
    tpin = serializers.CharField(max_length=10, required=False, allow_blank=True)
    billing_address = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    national_id = serializers.CharField(max_length=40, required=False, allow_blank=True)
    company_registration = serializers.CharField(max_length=80, required=False, allow_blank=True)
    representative_name = serializers.CharField(max_length=180, required=False, allow_blank=True)
    representative_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    missing_details = serializers.SerializerMethodField()
    locked_fields = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "full_name",
            "phone_number",
            "email",
            "status",
            "tenant_type",
            "tpin",
            "billing_address",
            "national_id",
            "identity_type",
            "identity_country",
            "company_registration",
            "representative_name",
            "representative_phone",
            "missing_details",
            "locked_fields",
        ]
        read_only_fields = ["full_name", "email", "status", "tenant_type"]

    def get_missing_details(self, obj):
        from apps.tenants.details import missing_details

        return missing_details(obj)

    def get_locked_fields(self, obj):
        # Type and country always have defaults; they describe the recorded
        # number, so they lock together with it.
        number_fields = ("identity_type", "identity_country")
        locked = [
            key
            for key in self.FILL_ONCE
            if key not in number_fields and str(getattr(obj, key) or "").strip()
        ]
        if "national_id" in locked:
            locked += number_fields
        return sorted(locked)

    def validate_phone_number(self, value):
        phone = normalize_phone_number(value)
        if not phone:
            raise serializers.ValidationError("Enter a valid phone number, such as 0971234567.")
        duplicate = Tenant.objects.filter(
            organization=self.instance.organization, phone_number=phone
        ).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError(
                "This number cannot be used. Ask your property manager to update it."
            )
        return phone

    def validate_tpin(self, value):
        value = value.strip()
        if value and not (len(value) == 10 and value.isascii() and value.isdigit()):
            raise serializers.ValidationError("A TPIN is 10 digits.")
        return value

    def validate_billing_address(self, value):
        return value.strip()

    def validate_national_id(self, value):
        return " ".join(value.split())

    def validate_identity_country(self, value):
        if len(value) != 2 or not value.isascii() or not value.isalpha():
            raise serializers.ValidationError("Use a two-letter country code, for example ZM.")
        return value.upper()

    def validate_representative_phone(self, value):
        if not value.strip():
            return ""
        phone = normalize_phone_number(value)
        if not phone:
            raise serializers.ValidationError("Enter a valid representative phone number.")
        return phone

    def validate(self, attrs):
        locked = set(self.get_locked_fields(self.instance))
        errors = {
            key: ["Already recorded. Ask your property manager to correct it."]
            for key in attrs
            if key in locked and attrs[key] != getattr(self.instance, key)
        }
        if errors:
            raise serializers.ValidationError(errors)
        # Clearing a document detail would block receipts; never allow it here.
        for key in ("tpin", "billing_address"):
            if key in attrs and not attrs[key] and getattr(self.instance, key):
                errors[key] = ["This detail is needed for your receipts and cannot be removed."]
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
