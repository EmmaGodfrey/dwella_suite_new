from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.common.viewsets import OrganizationScopedModelViewSet
from apps.integrations import smart_invoice

from .models import Invoice, Payment
from .serializers import (
    GenerateInvoicesSerializer,
    InvoiceDetailSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    RecordPaymentSerializer,
)
from .services import (
    apply_late_fees,
    first_of_month,
    generate_rent_invoices,
    month_bounds,
    record_payment,
    void_invoice,
)

ZERO = Decimal("0")


def money(value):
    """Format like the serializers' DecimalFields: a 2-place string."""
    return str(Decimal(value).quantize(Decimal("0.01")))


class InvoiceFilter(filters.FilterSet):
    tenant = filters.UUIDFilter(field_name="tenant__public_id")
    lease = filters.UUIDFilter(field_name="lease__public_id")
    property = filters.UUIDFilter(field_name="unit__property__public_id")
    overdue = filters.BooleanFilter(method="filter_overdue")
    unpaid = filters.BooleanFilter(method="filter_unpaid")

    class Meta:
        model = Invoice
        fields = ["status", "tenant", "lease", "property", "period_start", "overdue", "unpaid"]

    def filter_overdue(self, queryset, name, value):
        overdue = Q(status__in=Invoice.UNPAID_STATUSES, due_date__lt=timezone.localdate())
        return queryset.filter(overdue) if value else queryset.exclude(overdue)

    def filter_unpaid(self, queryset, name, value):
        unpaid = Q(status__in=Invoice.UNPAID_STATUSES)
        return queryset.filter(unpaid) if value else queryset.exclude(unpaid)


class InvoiceViewSet(OrganizationScopedModelViewSet):
    queryset = Invoice.objects.select_related(
        "tenant", "lease", "unit__property", "charged_for"
    ).prefetch_related("lines", "fiscal_receipts")
    filterset_class = InvoiceFilter
    search_fields = ["reference", "tenant__full_name", "tenant__phone_number", "unit__name"]
    ordering_fields = ["due_date", "issue_date", "total", "reference"]
    # Invoices are financial records: corrected by voiding, never deleted.
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return InvoiceDetailSerializer
        return InvoiceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.select_related("organization__smart_invoice").prefetch_related(
                "payments__recorded_by"
            )
        return queryset

    def detail_response(self, invoice, status=200):
        invoice = self.get_queryset().get(pk=invoice.pk)
        return Response(
            InvoiceDetailSerializer(invoice, context=self.get_serializer_context()).data,
            status=status,
        )

    @action(detail=True, methods=["post"], url_path="record-payment")
    def record_payment(self, request, public_id=None):
        invoice = self.get_object()
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        record_payment(
            invoice=invoice,
            amount=data["amount"],
            method=data["method"],
            paid_on=data.get("paid_on") or timezone.localdate(),
            reference=data["reference"].strip(),
            notes=data["notes"].strip(),
            recorded_by=request.user,
        )
        self.action = "retrieve"
        return self.detail_response(invoice, status=201)

    @action(detail=True, methods=["post"])
    def void(self, request, public_id=None):
        invoice = void_invoice(self.get_object())
        self.action = "retrieve"
        return self.detail_response(invoice)

    @action(detail=True, methods=["post"], url_path="send-to-zra")
    def send_to_zra(self, request, public_id=None):
        """Send (or resend) this invoice to ZRA Smart Invoice."""
        invoice = self.get_object()
        if not smart_invoice.ready_settings(invoice.organization):
            raise ValidationError({"fiscal_status": ["Turn on ZRA Smart Invoice first."]})
        receipts = invoice.fiscal_receipts.all()
        if not receipts.exists():
            if invoice.status == Invoice.Status.VOID:
                raise ValidationError({"fiscal_status": ["This invoice is void."]})
            with transaction.atomic():
                if smart_invoice.queue_sale_receipt(invoice) is None:
                    raise ValidationError(
                        {"fiscal_status": ["Deposits are not reported to ZRA."]}
                    )
        smart_invoice.resend_receipts(receipts)
        self.action = "retrieve"
        return self.detail_response(invoice)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        serializer = GenerateInvoicesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        period = serializer.validated_data["period"]
        organization = self.get_organization()
        created, skipped = generate_rent_invoices(organization, period)
        late_fees = apply_late_fees(organization)
        return Response(
            {
                "period": period.isoformat(),
                "created": created,
                "already_billed": skipped,
                "late_fees_added": late_fees,
            }
        )

    @action(detail=False, methods=["get"])
    def summary(self, request):
        today = timezone.localdate()
        first, last = month_bounds(first_of_month(today))
        invoices = self.get_queryset().exclude(status=Invoice.Status.VOID)
        unpaid = invoices.filter(status__in=Invoice.UNPAID_STATUSES)
        overdue = unpaid.filter(due_date__lt=today)
        outstanding = F("total") - F("amount_paid")
        billed = invoices.filter(issue_date__range=(first, last)).aggregate(
            total=Coalesce(Sum("total"), ZERO), count=Count("id")
        )
        payments = Payment.objects.filter(invoice__in=self.get_queryset())
        collected = payments.filter(paid_on__range=(first, last)).aggregate(
            total=Coalesce(Sum("amount"), ZERO)
        )
        # Rent counts toward the month it is for, so a late invoice run still
        # lands in the right month; one-off charges fall back to issue date.
        by_period = invoices.annotate(
            month=TruncMonth(Coalesce("period_start", "issue_date"))
        )
        # This month's invoices split three ways so the parts add up to what
        # was billed: already paid, still within terms, and past due.
        this_month = by_period.filter(month=first).aggregate(
            billed=Coalesce(Sum("total"), ZERO),
            paid=Coalesce(Sum("amount_paid"), ZERO),
            not_yet_due=Coalesce(Sum(outstanding, filter=Q(due_date__gte=today)), ZERO),
            overdue=Coalesce(Sum(outstanding, filter=Q(due_date__lt=today)), ZERO),
        )
        # Six months of billed vs collected, keyed by the month billed for.
        months = [first]
        for _ in range(5):
            months.insert(0, first_of_month(months[0] - timedelta(days=1)))
        by_month = {
            row["month"]: row
            for row in by_period.filter(month__gte=months[0])
            .values("month")
            .annotate(billed=Sum("total"), collected=Sum("amount_paid"))
        }
        return Response(
            {
                "month": first.isoformat(),
                "billed_this_month": money(billed["total"]),
                "invoices_this_month": billed["count"],
                "collected_this_month": money(collected["total"]),
                "outstanding": money(
                    unpaid.aggregate(total=Coalesce(Sum(outstanding), ZERO))["total"]
                ),
                "overdue": money(
                    overdue.aggregate(total=Coalesce(Sum(outstanding), ZERO))["total"]
                ),
                "overdue_count": overdue.count(),
                "month_breakdown": {key: money(value) for key, value in this_month.items()},
                "history": [
                    {
                        "month": month.isoformat(),
                        "billed": money(by_month.get(month, {}).get("billed") or ZERO),
                        "collected": money(by_month.get(month, {}).get("collected") or ZERO),
                    }
                    for month in months
                ],
            }
        )


class PaymentFilter(filters.FilterSet):
    tenant = filters.UUIDFilter(field_name="tenant__public_id")
    invoice = filters.UUIDFilter(field_name="invoice__public_id")

    class Meta:
        model = Payment
        fields = ["tenant", "invoice", "method"]


class PaymentViewSet(OrganizationScopedModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("invoice", "tenant", "recorded_by")
    filterset_class = PaymentFilter
    search_fields = ["receipt_number", "reference", "tenant__full_name"]
    ordering_fields = ["paid_on", "amount", "created_at"]
    # Payments are created through an invoice's record-payment action.
    http_method_names = ["get", "head", "options"]
