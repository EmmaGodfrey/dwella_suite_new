import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.references import next_reference
from apps.integrations import smart_invoice
from apps.leases.models import Lease

from .models import Invoice, InvoiceLine, Payment

CENT = Decimal("0.01")


@transaction.atomic
def reverse_payment(payment, *, reason, user):
    """Correct the ledger, keeping the original receipt and who corrected it."""
    invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.reversed_at:
        raise ValidationError({"reason": ["This payment has already been reversed."]})
    if not reason.strip():
        raise ValidationError({"reason": ["Explain why this payment is being reversed."]})
    payment.reversed_at = timezone.now()
    payment.reversal_reason = reason.strip()
    payment.reversed_by = user
    payment.save(update_fields=["reversed_at", "reversal_reason", "reversed_by", "updated_at"])
    refresh_totals(invoice)
    return payment


def month_bounds(period_start):
    last_day = calendar.monthrange(period_start.year, period_start.month)[1]
    return period_start, period_start.replace(day=last_day)


def refresh_totals(invoice):
    """Recompute stored total/paid/status from lines and payments."""
    invoice.total = invoice.lines.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    invoice.amount_paid = invoice.payments.filter(reversed_at__isnull=True).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    if invoice.status != Invoice.Status.VOID:
        if invoice.amount_paid <= 0:
            invoice.status = Invoice.Status.OPEN
        elif invoice.amount_paid < invoice.total:
            invoice.status = Invoice.Status.PARTIALLY_PAID
        else:
            invoice.status = Invoice.Status.PAID
    invoice.save(update_fields=["total", "amount_paid", "status", "updated_at"])
    return invoice


@transaction.atomic
def create_invoice(
    *,
    organization,
    tenant,
    lines,
    issue_date,
    due_date,
    lease=None,
    unit=None,
    period_start=None,
    charged_for=None,
    notes="",
):
    invoice = Invoice.objects.create(
        organization=organization,
        reference=next_reference(organization, Invoice, "INV"),
        tenant=tenant,
        lease=lease,
        unit=unit or (lease.unit if lease else None),
        period_start=period_start,
        issue_date=issue_date,
        due_date=due_date,
        charged_for=charged_for,
        notes=notes,
    )
    InvoiceLine.objects.bulk_create(InvoiceLine(invoice=invoice, **line) for line in lines)
    refresh_totals(invoice)
    smart_invoice.queue_sale_receipt(invoice)
    return invoice


def generate_rent_invoices(organization, period_start, today=None):
    """Issue one rent invoice per active lease covering the month.

    Safe to run again for the same month: leases that already have a live
    invoice for it are skipped. Returns (created, skipped) counts.
    """
    today = today or timezone.localdate()
    first, last = month_bounds(period_start.replace(day=1))
    leases = (
        Lease.objects.for_organization(organization)
        .filter(status=Lease.Status.ACTIVE, start_date__lte=last, end_date__gte=first)
        .select_related("tenant", "unit")
    )
    billed = set(
        Invoice.objects.filter(lease__in=leases, period_start=first)
        .exclude(status=Invoice.Status.VOID)
        .values_list("lease_id", flat=True)
    )
    # A renewal continues the same tenancy: when the lease it follows ended
    # mid-month and was billed for it, that month is not billed twice. (Only one
    # of the two is ever active, so only the earlier lease can be billed first.)
    billed_before = set(
        Invoice.objects.filter(
            lease_id__in=[lease.renewal_of_id for lease in leases if lease.renewal_of_id],
            period_start=first,
        )
        .exclude(status=Invoice.Status.VOID)
        .values_list("lease_id", flat=True)
    )
    created = 0
    for lease in leases:
        if lease.id in billed or lease.renewal_of_id in billed_before:
            continue
        # Never due before it is issued: a month billed late (e.g. a landlord
        # who joins mid-month) gets its grace period from today, so tenants
        # are not charged a late fee on an invoice they have only just received.
        due = max(first.replace(day=lease.rent_due_day), today)
        create_invoice(
            organization=organization,
            tenant=lease.tenant,
            lease=lease,
            period_start=first,
            issue_date=today,
            due_date=due,
            lines=[
                {
                    "kind": InvoiceLine.Kind.RENT,
                    "description": f"Rent · {first:%B %Y}",
                    "amount": lease.monthly_rent,
                }
            ],
        )
        created += 1
    return created, len(billed)


@transaction.atomic
def record_payment(*, invoice, amount, method, paid_on, reference="", notes="", recorded_by=None):
    # Lock the invoice so two people recording at once cannot overpay it.
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status == Invoice.Status.VOID:
        raise ValidationError({"invoice": ["This invoice is void."]})
    if amount <= 0:
        raise ValidationError({"amount": ["Amount must be more than zero."]})
    if amount > invoice.balance:
        raise ValidationError(
            {"amount": [f"Only {invoice.balance} is still owed on this invoice."]}
        )
    payment = Payment.objects.create(
        organization=invoice.organization,
        receipt_number=next_reference(invoice.organization, Payment, "RCT", field="receipt_number"),
        invoice=invoice,
        tenant=invoice.tenant,
        amount=amount,
        method=method,
        paid_on=paid_on,
        reference=reference,
        notes=notes,
        recorded_by=recorded_by,
    )
    refresh_totals(invoice)
    return payment


@transaction.atomic
def void_invoice(invoice):
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status == Invoice.Status.VOID:
        raise ValidationError({"status": ["This invoice is already void."]})
    if invoice.payments.filter(reversed_at__isnull=True).exists():
        raise ValidationError({"status": ["An invoice with payments cannot be voided."]})
    invoice.status = Invoice.Status.VOID
    invoice.voided_at = timezone.now()
    invoice.save(update_fields=["status", "voided_at", "updated_at"])
    smart_invoice.queue_refund_receipt(invoice)
    return invoice


def late_fee_follow_ups():
    return Invoice.objects.filter(
        charged_for__isnull=False, lines__kind=InvoiceLine.Kind.LATE_FEE
    ).exclude(status=Invoice.Status.VOID)


def apply_late_fees(organization, today=None):
    """Add each lease's late fee to unpaid rent invoices past their grace period.

    A fee is added at most once per invoice. Invoices already sent to ZRA
    cannot change, so their fee goes on a follow-up invoice instead.
    Returns how many were added.
    """
    today = today or timezone.localdate()
    candidates = (
        Invoice.objects.for_organization(organization)
        .filter(
            status__in=Invoice.UNPAID_STATUSES,
            lease__late_fee_percent__gt=0,
            period_start__isnull=False,
        )
        .exclude(lines__kind=InvoiceLine.Kind.LATE_FEE)
        .exclude(pk__in=late_fee_follow_ups().values("charged_for"))
        .select_related("lease", "tenant", "unit")
    )
    added = 0
    for invoice in candidates:
        lease = invoice.lease
        if today <= invoice.due_date + timedelta(days=lease.late_fee_grace_days):
            continue
        fee = (lease.monthly_rent * lease.late_fee_percent / 100).quantize(CENT, ROUND_HALF_UP)
        with transaction.atomic():
            locked = Invoice.objects.select_for_update().get(pk=invoice.pk)
            if (
                locked.lines.filter(kind=InvoiceLine.Kind.LATE_FEE).exists()
                or late_fee_follow_ups().filter(charged_for=locked).exists()
            ):
                continue
            description = (
                f"Late fee · {lease.late_fee_percent.normalize()}%"
                f" after {lease.late_fee_grace_days} days"
            )
            if locked.fiscal_receipts.exclude(status="cancelled").exists():
                create_invoice(
                    organization=organization,
                    tenant=locked.tenant,
                    lease=lease,
                    unit=locked.unit,
                    issue_date=today,
                    due_date=today,
                    charged_for=locked,
                    lines=[
                        {
                            "kind": InvoiceLine.Kind.LATE_FEE,
                            "description": f"{description} on {locked.reference}",
                            "amount": fee,
                        }
                    ],
                )
            else:
                InvoiceLine.objects.create(
                    invoice=locked,
                    kind=InvoiceLine.Kind.LATE_FEE,
                    description=description,
                    amount=fee,
                )
                refresh_totals(locked)
        added += 1
    return added


def first_of_month(value):
    return date(value.year, value.month, 1)
