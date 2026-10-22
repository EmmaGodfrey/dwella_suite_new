import re
from datetime import date

from django.utils import timezone
from rest_framework import serializers

from apps.common.serializers import OrganizationScopedSerializer
from apps.integrations.models import FiscalReceipt
from apps.integrations.serializers import FiscalReceiptSerializer
from apps.leases.models import Lease
from apps.tenants.models import Tenant

from .models import Invoice, InvoiceLine, Payment
from .services import create_invoice


def scoped(serializer, model):
    view = serializer.context.get("view")
    if view is None:
        return model.objects.none()
    return model.objects.for_organization(view.get_organization())


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ["kind", "description", "amount"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be more than zero.")
        return value


class PaymentSerializer(OrganizationScopedSerializer):
    invoice_id = serializers.UUIDField(source="invoice.public_id", read_only=True)
    invoice_reference = serializers.CharField(source="invoice.reference", read_only=True)
    tenant_name = serializers.CharField(source="tenant.full_name", read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "organization_id",
            "receipt_number",
            "invoice_id",
            "invoice_reference",
            "tenant_name",
            "amount",
            "method",
            "paid_on",
            "reference",
            "notes",
            "recorded_by_name",
            "reversed_at",
            "reversal_reason",
            "created_at",
        ]
        read_only_fields = fields

    def get_recorded_by_name(self, obj):
        user = obj.recorded_by
        return (user.get_full_name() or user.username) if user else None


class ReceiptSerializer(PaymentSerializer):
    issuer = serializers.SerializerMethodField()
    property_name = serializers.CharField(source="invoice.unit.property.name", default=None)
    unit_name = serializers.CharField(source="invoice.unit.name", default=None)
    tenant_phone = serializers.CharField(source="tenant.phone_number", read_only=True)
    invoice_total = serializers.DecimalField(
        source="invoice.total", max_digits=12, decimal_places=2, read_only=True
    )
    current_balance = serializers.DecimalField(
        source="invoice.balance", max_digits=12, decimal_places=2, read_only=True
    )
    reversed_by_name = serializers.SerializerMethodField()

    class Meta(PaymentSerializer.Meta):
        fields = [
            *PaymentSerializer.Meta.fields,
            "issuer",
            "property_name",
            "unit_name",
            "tenant_phone",
            "invoice_total",
            "current_balance",
            "reversed_by_name",
        ]
        read_only_fields = fields

    def get_issuer(self, obj):
        org = obj.organization
        return {
            "name": str(org),
            "address": org.address,
            "town": org.town,
            "phone_number": org.phone_number,
            "email": org.email,
            "currency": org.currency,
        }

    def get_reversed_by_name(self, obj):
        user = obj.reversed_by
        return (user.get_full_name() or user.username) if user else None


class ReversePaymentSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, min_length=5)


class InvoiceSerializer(OrganizationScopedSerializer):
    tenant = serializers.SlugRelatedField(slug_field="public_id", queryset=Tenant.objects.none())
    lease = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Lease.objects.none(), required=False, allow_null=True
    )
    tenant_name = serializers.CharField(source="tenant.full_name", read_only=True)
    tenant_phone = serializers.CharField(source="tenant.phone_number", read_only=True)
    lease_reference = serializers.CharField(source="lease.reference", read_only=True, default=None)
    unit_name = serializers.CharField(source="unit.name", read_only=True, default=None)
    property_name = serializers.CharField(source="unit.property.name", read_only=True, default=None)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    days_overdue = serializers.SerializerMethodField()
    fiscal_status = serializers.SerializerMethodField()
    charged_for_id = serializers.UUIDField(
        source="charged_for.public_id", read_only=True, default=None
    )
    charged_for_reference = serializers.CharField(
        source="charged_for.reference", read_only=True, default=None
    )
    issue_date = serializers.DateField(required=False)
    lines = InvoiceLineSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "organization_id",
            "reference",
            "tenant",
            "tenant_name",
            "tenant_phone",
            "lease",
            "lease_reference",
            "unit_name",
            "property_name",
            "period_start",
            "issue_date",
            "due_date",
            "total",
            "amount_paid",
            "balance",
            "status",
            "days_overdue",
            "fiscal_status",
            "charged_for_id",
            "charged_for_reference",
            "lines",
            "notes",
            "voided_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "reference",
            "period_start",
            "total",
            "amount_paid",
            "status",
            "voided_at",
        ]

    def get_fields(self):
        fields = super().get_fields()
        fields["tenant"].queryset = scoped(self, Tenant)
        fields["lease"].queryset = scoped(self, Lease)
        if self.instance is not None:
            # Issued invoices are records: only the note can change. Corrections
            # are made by voiding and re-issuing.
            for name in ("tenant", "lease", "issue_date", "due_date", "lines"):
                fields[name].read_only = True
        return fields

    def get_days_overdue(self, obj):
        if obj.status not in Invoice.UNPAID_STATUSES:
            return 0
        return max(0, (timezone.localdate() - obj.due_date).days)

    def get_fiscal_status(self, obj):
        # Where the invoice stands with ZRA Smart Invoice; None when it was
        # never sent (Smart Invoice off, or a deposit-only invoice).
        receipts = {receipt.kind: receipt for receipt in obj.fiscal_receipts.all()}
        refund = receipts.get(FiscalReceipt.Kind.REFUND)
        sale = receipts.get(FiscalReceipt.Kind.SALE)
        if refund and refund.status != FiscalReceipt.Status.ISSUED:
            return refund.status
        if refund:
            return "credited"
        return sale.status if sale else None

    def validate_lines(self, value):
        if not value:
            raise serializers.ValidationError("Add at least one charge.")
        return value

    def validate(self, attrs):
        if self.instance is not None:
            return attrs
        lease = attrs.get("lease")
        if lease and lease.tenant_id != attrs["tenant"].id:
            raise serializers.ValidationError({"lease": ["This lease belongs to another tenant."]})
        attrs.setdefault("issue_date", timezone.localdate())
        if attrs["due_date"] < attrs["issue_date"]:
            raise serializers.ValidationError(
                {"due_date": ["Due date cannot be before the issue date."]}
            )
        return attrs

    def create(self, validated_data):
        return create_invoice(**validated_data)


class InvoiceDetailSerializer(InvoiceSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    fiscal_receipts = FiscalReceiptSerializer(many=True, read_only=True)
    issuer = serializers.SerializerMethodField()
    tenant_tpin = serializers.CharField(source="tenant.tpin", read_only=True)
    tenant_email = serializers.CharField(source="tenant.email", read_only=True)

    class Meta(InvoiceSerializer.Meta):
        fields = [
            *InvoiceSerializer.Meta.fields,
            "tenant_tpin",
            "tenant_email",
            "payments",
            "fiscal_receipts",
            "issuer",
        ]

    def get_issuer(self, obj):
        """Who the printed invoice is from."""
        organization = obj.organization
        config = getattr(organization, "smart_invoice", None)
        return {
            "name": str(organization),
            "address": organization.address,
            "town": organization.town,
            "country": organization.country,
            "phone_number": organization.phone_number,
            "email": organization.email,
            "tpin": config.tpin if config else None,
        }


class RecordPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    method = serializers.ChoiceField(choices=Payment.Method.choices)
    paid_on = serializers.DateField(required=False)
    reference = serializers.CharField(max_length=80, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_paid_on(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Payment date cannot be in the future.")
        return value


class GenerateInvoicesSerializer(serializers.Serializer):
    period = serializers.CharField(help_text="Month to bill, as YYYY-MM.")

    def validate_period(self, value):
        match = re.fullmatch(r"(\d{4})-(\d{2})", value.strip())
        if not match or not 1 <= int(match.group(2)) <= 12 or int(match.group(1)) < 1:
            raise serializers.ValidationError("Use the format YYYY-MM, for example 2026-11.")
        period = date(int(match.group(1)), int(match.group(2)), 1)
        today = timezone.localdate()
        months_ahead = (period.year - today.year) * 12 + period.month - today.month
        if months_ahead > 1:
            raise serializers.ValidationError("You can bill this month or next month at most.")
        return period
