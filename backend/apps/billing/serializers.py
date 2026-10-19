import re
from datetime import date

from django.utils import timezone
from rest_framework import serializers

from apps.common.serializers import OrganizationScopedSerializer
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
            "created_at",
        ]
        read_only_fields = fields

    def get_recorded_by_name(self, obj):
        user = obj.recorded_by
        return (user.get_full_name() or user.username) if user else None


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

    class Meta(InvoiceSerializer.Meta):
        fields = [*InvoiceSerializer.Meta.fields, "payments"]


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
        if not match or not 1 <= int(match.group(2)) <= 12:
            raise serializers.ValidationError("Use the format YYYY-MM, for example 2026-11.")
        period = date(int(match.group(1)), int(match.group(2)), 1)
        today = timezone.localdate()
        months_ahead = (period.year - today.year) * 12 + period.month - today.month
        if months_ahead > 1:
            raise serializers.ValidationError("You can bill this month or next month at most.")
        return period
