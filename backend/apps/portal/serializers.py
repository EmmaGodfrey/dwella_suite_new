"""Tenant-facing shapes.

These list fields explicitly rather than reusing the manager serializers, so a
field added for managers (notes, internal costs, identity numbers, who recorded
a payment) never reaches a tenant by accident.
"""

from django.utils import timezone
from rest_framework import serializers

from apps.billing.models import Invoice, InvoiceLine, Payment
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


class ReceiptSerializer(PaymentSerializer):
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
            "tenant_name",
            "property_name",
            "unit_name",
            "invoice_total",
            "current_balance",
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
    phone_number = serializers.CharField(max_length=40)

    class Meta:
        model = Tenant
        fields = ["id", "full_name", "phone_number", "email", "status"]
        read_only_fields = ["full_name", "email", "status"]

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
