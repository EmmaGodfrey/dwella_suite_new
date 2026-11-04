"""Bringing an existing tenancy into Dwella without inventing new billing.

Three facts can be recorded per active lease: what the tenant already owes, the
month rent is already paid up to, and a deposit already held. Old debt is one
ordinary invoice, so payments, receipts, arrears and statements all keep working.
No old month is billed again and nothing here issues a receipt.
"""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.leases.models import Lease

from . import deposits
from .models import DepositEntry, Invoice, InvoiceLine
from .services import create_invoice, first_of_month

DESCRIPTION = "Balance brought forward"


def _require_active(lease):
    if lease.status != Lease.Status.ACTIVE:
        raise ValidationError({"lease": ["Activate this lease first."]})


def live_opening_balance(lease):
    return (
        Invoice.objects.filter(lease=lease, is_opening_balance=True)
        .exclude(status=Invoice.Status.VOID)
        .first()
    )


@transaction.atomic
def record_opening_balance(lease, *, amount, owed_since, note=""):
    """One invoice for everything owed before Dwella. Void it to correct it."""
    if amount is None or amount <= 0:
        raise ValidationError({"owes": ["Enter an amount more than zero."]})
    lease = deposits.lock(lease)
    _require_active(lease)
    if owed_since > timezone.localdate():
        raise ValidationError({"owed_since": ["The date cannot be in the future."]})
    existing = live_opening_balance(lease)
    if existing:
        raise ValidationError(
            {"owes": [f"{existing.reference} already holds this balance. Void it to change it."]}
        )
    return create_invoice(
        organization=lease.organization,
        tenant=lease.tenant,
        lease=lease,
        # Dated when it fell due, so arrears ageing and statements stay truthful.
        issue_date=owed_since,
        due_date=owed_since,
        notes=note,
        is_opening_balance=True,
        lines=[{"kind": InvoiceLine.Kind.OTHER, "description": DESCRIPTION, "amount": amount}],
    )


def rent_paid_up_to(lease):
    """The last month already paid for, or None when every month is billed."""
    if not lease.billed_from:
        return None
    return first_of_month(lease.billed_from - timedelta(days=1))


@transaction.atomic
def set_rent_paid_up_to(lease, month):
    """Stop billing up to and including `month`; None bills every month again."""
    lease = deposits.lock(lease)
    _require_active(lease)
    if month is None:
        lease.billed_from = None
        lease.save(update_fields=["billed_from", "updated_at"])
        return lease
    this_month = first_of_month(timezone.localdate())
    month = first_of_month(month)
    if month < this_month:
        raise ValidationError({"rent_paid_up_to": ["Choose this month or a later one."]})
    if month > first_of_month(lease.end_date):
        raise ValidationError({"rent_paid_up_to": ["Choose a month before the lease ends."]})
    billed_from = first_of_month(month + timedelta(days=32))
    # Auto-billing may have run already. Hiding an unpaid invoice would leave the
    # tenant owing rent they paid, so the manager voids it deliberately.
    unpaid = (
        Invoice.objects.filter(
            lease=lease,
            period_start__gte=this_month,
            period_start__lt=billed_from,
            status__in=Invoice.UNPAID_STATUSES,
        )
        .order_by("period_start")
        .values_list("reference", flat=True)
    )
    if unpaid:
        raise ValidationError(
            {"rent_paid_up_to": [f"Void {', '.join(unpaid)} first: it bills a month already paid."]}
        )
    lease.billed_from = billed_from
    lease.save(update_fields=["billed_from", "updated_at"])
    return lease


@transaction.atomic
def record_deposit_held(lease, *, amount, occurred_on, user):
    """The deposit's first ledger entry; later changes use the deposit drawer."""
    if amount is None or amount <= 0:
        raise ValidationError({"deposit_held": ["Enter an amount more than zero."]})
    lease = deposits.lock(lease)
    _require_active(lease)
    if DepositEntry.objects.filter(lease=lease).exists():
        raise ValidationError(
            {"deposit_held": ["This deposit is already recorded. Open the lease's deposit."]}
        )
    return deposits.record_opening(
        lease,
        amount=amount,
        occurred_on=occurred_on,
        note="Recorded when the tenancy moved to Dwella.",
        user=user,
    )
