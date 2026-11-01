"""Security deposits: money held for the tenant, separate from rent.

Dwella records the deposit; it does not hold or protect the funds. Every
change locks the lease first so two people cannot spend the same balance.
Held = sum of ledger entries; reserved = open deductions; available = held -
reserved. Deductions never reduce what is held until they are applied.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch, Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.leases.models import Lease

from .models import DepositDeduction, DepositEntry, DepositEvidence, Invoice, InvoiceLine

ZERO = Decimal("0")


def _notify(target, event, **options):
    # Notices never block or undo a deposit change.
    from apps.notifications.events import safe_enqueue

    safe_enqueue(target, event, **options)


def _total(queryset, field="amount"):
    return queryset.aggregate(total=Sum(field))["total"] or ZERO


def lock(lease):
    return Lease.objects.select_for_update().get(pk=lease.pk)


def held(lease):
    return _total(DepositEntry.objects.filter(lease=lease))


def reserved(lease):
    return _total(
        DepositDeduction.objects.filter(lease=lease, status__in=DepositDeduction.OPEN_STATUSES)
    )


def requested_unpaid(lease):
    """Deposit still owed on issued, unpaid deposit invoices."""
    rows = (
        Invoice.objects.filter(lease=lease, status__in=Invoice.UNPAID_STATUSES)
        .filter(lines__kind=InvoiceLine.Kind.DEPOSIT)
        .distinct()
    )
    return sum((invoice.balance for invoice in rows), ZERO)


def summary(lease):
    entries = list(DepositEntry.objects.filter(lease=lease).select_related("deduction"))
    total_held = sum((entry.amount for entry in entries), ZERO)
    total_reserved = reserved(lease)
    return {
        "agreed": lease.deposit_amount,
        "held": total_held,
        "collected": sum(
            (
                e.amount
                for e in entries
                if e.kind
                in (
                    DepositEntry.Kind.COLLECTED,
                    DepositEntry.Kind.OPENING,
                    DepositEntry.Kind.TRANSFER_IN,
                )
            ),
            ZERO,
        ),
        "reserved": total_reserved,
        "available": total_held - total_reserved,
        "requested_unpaid": requested_unpaid(lease),
        "entries": entries,
        # File contents are only read when someone opens one.
        "deductions": list(
            DepositDeduction.objects.filter(lease=lease).prefetch_related(
                Prefetch("evidence", queryset=DepositEvidence.objects.defer("content"))
            )
        ),
    }


def sync_invoice(invoice, deposit_total):
    """Keep 'collected' entries in step with what was paid on a deposit invoice.

    Payments settle other lines (rent, charges) first and the deposit last, so
    a part payment on a mixed invoice is never counted as deposit too early.
    Called from refresh_totals inside the invoice lock; reversals post a
    negative correction rather than editing history.
    """
    if not invoice.lease_id:
        return
    other = invoice.total - deposit_total
    target = min(max(invoice.amount_paid - other, ZERO), deposit_total)
    if invoice.status == Invoice.Status.VOID:
        target = ZERO
    current = _total(DepositEntry.objects.filter(invoice=invoice, kind=DepositEntry.Kind.COLLECTED))
    if target != current:
        DepositEntry.objects.create(
            organization_id=invoice.organization_id,
            lease_id=invoice.lease_id,
            kind=DepositEntry.Kind.COLLECTED,
            amount=target - current,
            occurred_on=timezone.localdate(),
            invoice=invoice,
            reference=invoice.reference,
            note="" if target > current else "Payment reversed",
        )


@transaction.atomic
def request_deposit(lease, *, user, amount=None):
    """Issue a deposit invoice for what is still to be collected."""
    from .services import create_invoice

    lease = lock(lease)
    if lease.status == Lease.Status.ENDED:
        raise ValidationError({"lease": ["This lease has ended."]})
    outstanding = lease.deposit_amount - held(lease) - requested_unpaid(lease)
    amount = outstanding if amount is None else amount
    if amount <= 0 or outstanding <= 0:
        raise ValidationError(
            {"amount": ["Nothing more to request: the agreed deposit is held or already invoiced."]}
        )
    if amount > outstanding:
        raise ValidationError({"amount": [f"Only {outstanding} is still to be requested."]})
    today = timezone.localdate()
    top_up = held(lease) > 0
    return create_invoice(
        organization=lease.organization,
        tenant=lease.tenant,
        lease=lease,
        issue_date=today,
        due_date=max(today, lease.start_date),
        lines=[
            {
                "kind": InvoiceLine.Kind.DEPOSIT,
                "description": f"Security deposit{' top-up' if top_up else ''} · {lease.reference}"
                " · held for the tenant, refundable",
                "amount": amount,
            }
        ],
    )


def _positive(amount, field="amount"):
    if amount is None or amount <= 0:
        raise ValidationError({field: ["Enter an amount more than zero."]})


@transaction.atomic
def record_opening(lease, *, amount, occurred_on, note, user):
    """A deposit paid before the tenancy came into Dwella: no new receipt."""
    _positive(amount)
    lease = lock(lease)
    if occurred_on > timezone.localdate():
        raise ValidationError({"occurred_on": ["The date cannot be in the future."]})
    return DepositEntry.objects.create(
        organization=lease.organization,
        lease=lease,
        kind=DepositEntry.Kind.OPENING,
        amount=amount,
        occurred_on=occurred_on,
        note=note,
        recorded_by=user,
    )


@transaction.atomic
def propose_deduction(lease, *, amount, reason, details, user):
    _positive(amount)
    lease = lock(lease)
    if not reason.strip():
        raise ValidationError({"reason": ["Say what the deduction is for."]})
    available = held(lease) - reserved(lease)
    if amount > available:
        raise ValidationError({"amount": [f"Only {available} of the deposit is available."]})
    row = DepositDeduction.objects.create(
        organization=lease.organization,
        lease=lease,
        amount=amount,
        reason=reason.strip(),
        details=details.strip(),
        proposed_by=user,
    )
    _notify(row, "deposit.deduction_proposed", tenant_only=True, state=row.status, actor=user)
    return row


def _locked_deduction(deduction):
    lock(deduction.lease)
    return DepositDeduction.objects.select_for_update().get(pk=deduction.pk)


@transaction.atomic
def respond_to_deduction(deduction, *, accept, note):
    """The tenant's answer. Changing their mind is allowed until it is applied."""
    deduction = _locked_deduction(deduction)
    if deduction.status not in DepositDeduction.OPEN_STATUSES:
        raise ValidationError({"status": ["This deduction has already been decided."]})
    if not accept and not note.strip():
        raise ValidationError({"note": ["Say why you disagree."]})
    deduction.status = (
        DepositDeduction.Status.ACCEPTED if accept else DepositDeduction.Status.DISPUTED
    )
    deduction.tenant_note = note.strip()
    deduction.responded_at = timezone.now()
    deduction.save(update_fields=["status", "tenant_note", "responded_at", "updated_at"])
    _notify(
        deduction,
        "deposit.deduction_answered",
        managers_only=True,
        state=deduction.status,
        # A tenant may change their answer; each answer is its own notice.
        suffix=f"{deduction.status}:{deduction.responded_at.timestamp():.0f}",
    )
    return deduction


@transaction.atomic
def apply_deduction(deduction, *, user, resolution_note=""):
    deduction = _locked_deduction(deduction)
    if deduction.status == DepositDeduction.Status.PROPOSED:
        raise ValidationError({"status": ["Wait for the tenant to accept or dispute it."]})
    if deduction.status == DepositDeduction.Status.DISPUTED and not resolution_note.strip():
        raise ValidationError(
            {"resolution_note": ["The tenant disputed this. Record how it was resolved."]}
        )
    if deduction.status not in DepositDeduction.OPEN_STATUSES:
        raise ValidationError({"status": ["This deduction has already been decided."]})
    # Reservations (this one included) must still be covered by what is held.
    if held(deduction.lease) < reserved(deduction.lease):
        raise ValidationError({"amount": ["The deposit no longer covers this deduction."]})
    deduction.status = DepositDeduction.Status.APPLIED
    deduction.resolution_note = resolution_note.strip()
    deduction.decided_by = user
    deduction.decided_at = timezone.now()
    deduction.save(
        update_fields=["status", "resolution_note", "decided_by", "decided_at", "updated_at"]
    )
    DepositEntry.objects.create(
        organization_id=deduction.organization_id,
        lease_id=deduction.lease_id,
        kind=DepositEntry.Kind.DEDUCTION,
        amount=-deduction.amount,
        occurred_on=timezone.localdate(),
        deduction=deduction,
        note=deduction.reason,
        recorded_by=user,
    )
    _notify(
        deduction, "deposit.deduction_applied", tenant_only=True, state=deduction.status, actor=user
    )
    return deduction


@transaction.atomic
def withdraw_deduction(deduction, *, user):
    deduction = _locked_deduction(deduction)
    if deduction.status not in DepositDeduction.OPEN_STATUSES:
        raise ValidationError({"status": ["This deduction has already been decided."]})
    deduction.status = DepositDeduction.Status.WITHDRAWN
    deduction.decided_by = user
    deduction.decided_at = timezone.now()
    deduction.save(update_fields=["status", "decided_by", "decided_at", "updated_at"])
    return deduction


@transaction.atomic
def record_refund(lease, *, amount, method, reference, paid_on, note, user):
    """A refund the manager has actually paid; disputed amounts stay reserved."""
    _positive(amount)
    lease = lock(lease)
    if paid_on > timezone.localdate():
        raise ValidationError({"paid_on": ["The date cannot be in the future."]})
    available = held(lease) - reserved(lease)
    if amount > available:
        raise ValidationError({"amount": [f"Only {available} is available to refund."]})
    entry = DepositEntry.objects.create(
        organization=lease.organization,
        lease=lease,
        kind=DepositEntry.Kind.REFUND,
        amount=-amount,
        occurred_on=paid_on,
        method=method,
        reference=reference.strip(),
        note=note.strip(),
        recorded_by=user,
    )
    _notify(entry, "deposit.refund_recorded", tenant_only=True, actor=user)
    return entry


def carry_over_to_renewal(renewal, previous):
    """On renewal the unreserved deposit moves to the new lease, once.

    Called inside activate_lease's lock on both leases. Open deductions stay
    with the old lease until they are decided."""
    if DepositEntry.objects.filter(lease=renewal, kind=DepositEntry.Kind.TRANSFER_IN).exists():
        return
    amount = held(previous) - reserved(previous)
    if amount <= 0:
        return
    today = timezone.localdate()
    common = {"organization_id": previous.organization_id, "occurred_on": today}
    DepositEntry.objects.bulk_create(
        [
            DepositEntry(
                lease=previous,
                kind=DepositEntry.Kind.TRANSFER_OUT,
                amount=-amount,
                reference=renewal.reference,
                **common,
            ),
            DepositEntry(
                lease=renewal,
                kind=DepositEntry.Kind.TRANSFER_IN,
                amount=amount,
                reference=previous.reference,
                **common,
            ),
        ]
    )


@transaction.atomic
def add_evidence(deduction, *, upload, user):
    """Attach a photo or PDF (quote, receipt) to an undecided deduction.

    Images are re-encoded to JPEG, which strips location and camera metadata;
    PDFs must open in the isolated PDF reader. Nothing is stored unchecked."""
    import hashlib
    from pathlib import PurePath

    from apps.documents.files import MAX_PHOTO_BYTES, clean_image, inspect_pdf, read_upload

    deduction = _locked_deduction(deduction)
    if deduction.status not in DepositDeduction.OPEN_STATUSES:
        raise ValidationError({"file": ["This deduction has already been decided."]})
    if deduction.evidence.count() >= DepositEvidence.MAX_PER_DEDUCTION:
        raise ValidationError(
            {"file": [f"Add up to {DepositEvidence.MAX_PER_DEDUCTION} files per deduction."]}
        )
    raw = read_upload(upload, MAX_PHOTO_BYTES)
    stem = PurePath(getattr(upload, "name", "") or "evidence").stem[:100] or "evidence"
    if raw.startswith(b"%PDF-"):
        inspect_pdf(raw, render=False)
        content, content_type, name = raw, "application/pdf", f"{stem}.pdf"
    else:
        content, content_type, name = clean_image(raw, photo=True), "image/jpeg", f"{stem}.jpg"
    return DepositEvidence.objects.create(
        organization_id=deduction.organization_id,
        deduction=deduction,
        name=name,
        content_type=content_type,
        content=content,
        size=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        uploaded_by=user,
    )


def tenant_visible(queryset):
    """Withdrawn proposals are hidden from tenants; everything else is shown."""
    return queryset.filter(~Q(status=DepositDeduction.Status.WITHDRAWN))
