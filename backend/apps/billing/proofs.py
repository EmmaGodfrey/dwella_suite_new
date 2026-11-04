"""Payment proof: a tenant says they paid directly; a manager confirms it.

A proof never changes a balance by itself. Only a manager's explicit
confirmation records a payment, and it goes through record_payment like any
manual payment. Every change locks the invoice first, then the proof, so a
confirmation cannot race a second confirmation or another payment.

The same operations will back the WhatsApp flow; nothing here knows which
channel the request came from beyond the stored label.
"""

import hashlib
from pathlib import PurePath

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.references import next_reference

from .models import Invoice, PaymentProof, PaymentProofFile

ALLOWED_METHODS = {value for value, _ in PaymentProof.METHODS}


def _notify(proof, event, **options):
    # Notices never block or undo a proof decision.
    from apps.notifications.events import safe_enqueue

    safe_enqueue(proof, event, **options)


def clean_file(upload):
    from apps.documents.files import MAX_PHOTO_BYTES, clean_image, inspect_pdf, read_upload

    raw = read_upload(upload, MAX_PHOTO_BYTES)
    stem = PurePath(getattr(upload, "name", "") or "proof").stem[:100] or "proof"
    if raw.startswith(b"%PDF-"):
        inspect_pdf(raw, render=False)
        return raw, "application/pdf", f"{stem}.pdf"
    # Re-encoding drops location and camera metadata.
    return clean_image(raw, photo=True), "image/jpeg", f"{stem}.jpg"


def _store_files(proof, uploads, user):
    if len(uploads) > PaymentProof.MAX_FILES:
        raise ValidationError({"files": [f"Attach up to {PaymentProof.MAX_FILES} files."]})
    # Check every file before saving any, so a bad one leaves nothing behind.
    cleaned = [clean_file(upload) for upload in uploads]
    PaymentProofFile.objects.bulk_create(
        [
            PaymentProofFile(
                organization_id=proof.organization_id,
                proof=proof,
                revision=proof.revision,
                name=name,
                content_type=content_type,
                content=content,
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                uploaded_by=user,
            )
            for content, content_type, name in cleaned
        ]
    )


def _check_facts(invoice, *, amount, method, paid_on, reference, uploads, ignore=None):
    if invoice.status not in Invoice.UNPAID_STATUSES:
        raise ValidationError({"invoice": [f"Nothing is owed on {invoice.reference}."]})
    if amount is None or amount <= 0:
        raise ValidationError({"amount": ["Enter an amount more than zero."]})
    if amount > invoice.balance:
        raise ValidationError(
            {"amount": [f"Only {invoice.balance} is owed on {invoice.reference}."]}
        )
    if method not in ALLOWED_METHODS:
        raise ValidationError({"method": ["Choose how you paid."]})
    if paid_on > timezone.localdate():
        raise ValidationError({"paid_on": ["The payment date cannot be in the future."]})
    if not uploads and not reference.strip():
        raise ValidationError(
            {"files": ["Attach a screenshot or receipt, or enter the transaction reference."]}
        )
    open_proofs = invoice.payment_proofs.filter(status__in=PaymentProof.OPEN_STATUSES)
    if ignore is not None:
        open_proofs = open_proofs.exclude(pk=ignore.pk)
    if open_proofs.count() >= PaymentProof.MAX_OPEN_PER_INVOICE:
        raise ValidationError(
            {"invoice": ["Wait for your property manager to review the payments already sent."]}
        )


@transaction.atomic
def submit(
    invoice, *, user, amount, method, paid_on, reference="", note="", uploads=(), channel="portal"
):
    """Called with an invoice already limited to the tenant's own records."""
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    uploads = list(uploads)
    _check_facts(
        invoice,
        amount=amount,
        method=method,
        paid_on=paid_on,
        reference=reference,
        uploads=uploads,
    )
    proof = PaymentProof.objects.create(
        organization=invoice.organization,
        number=next_reference(invoice.organization, PaymentProof, "PRF", field="number"),
        invoice=invoice,
        tenant=invoice.tenant,
        submitted_by=user,
        channel=channel,
        amount=amount,
        method=method,
        paid_on=paid_on,
        reference=reference.strip(),
        note=note.strip(),
        submitted_at=timezone.now(),
    )
    _store_files(proof, uploads, user)
    _notify(proof, "proof.submitted", managers_only=True, suffix="1", actor=user)
    return proof


def _locked(proof):
    Invoice.objects.select_for_update().get(pk=proof.invoice_id)
    return PaymentProof.objects.select_for_update().select_related("invoice").get(pk=proof.pk)


@transaction.atomic
def cancel(proof, *, user):
    proof = _locked(proof)
    if proof.status not in PaymentProof.OPEN_STATUSES:
        raise ValidationError({"status": ["This payment has already been reviewed."]})
    proof.status = PaymentProof.Status.CANCELLED
    proof.save(update_fields=["status", "updated_at"])
    return proof


@transaction.atomic
def resubmit(proof, *, user, amount, method, paid_on, reference="", note="", uploads=()):
    """Answer a manager's question with corrected details or more files."""
    proof = _locked(proof)
    if proof.status != PaymentProof.Status.NEEDS_INFORMATION:
        raise ValidationError({"status": ["Only a payment with a question can be resent."]})
    uploads = list(uploads)
    existing = proof.files.count()
    if existing + len(uploads) > PaymentProof.MAX_FILES * 2:
        raise ValidationError({"files": ["This payment already has enough files."]})
    has_files = bool(uploads) or existing > 0
    _check_facts(
        proof.invoice,
        amount=amount,
        method=method,
        paid_on=paid_on,
        reference=reference,
        uploads=[True] if has_files else [],
        ignore=proof,
    )
    proof.history = [
        *proof.history,
        {
            "revision": proof.revision,
            "amount": f"{proof.amount:.2f}",
            "method": proof.method,
            "paid_on": proof.paid_on.isoformat(),
            "reference": proof.reference,
            "note": proof.note,
            "submitted_at": proof.submitted_at.isoformat(),
            "question": proof.review_note,
        },
    ]
    proof.revision += 1
    proof.amount, proof.method, proof.paid_on = amount, method, paid_on
    proof.reference, proof.note = reference.strip(), note.strip()
    proof.status = PaymentProof.Status.SUBMITTED
    proof.submitted_at = timezone.now()
    proof.review_note = ""
    proof.save()
    if uploads:
        _store_files(proof, uploads, user)
    _notify(proof, "proof.submitted", managers_only=True, suffix=str(proof.revision), actor=user)
    return proof


@transaction.atomic
def confirm(proof, *, user):
    """The manager checked the money arrived: record one payment and receipt."""
    from .services import record_payment

    proof = _locked(proof)
    if proof.status == PaymentProof.Status.CONFIRMED:
        return proof  # A repeated click returns the same result.
    if proof.status != PaymentProof.Status.SUBMITTED:
        raise ValidationError({"status": ["This payment is not waiting for confirmation."]})
    invoice = proof.invoice
    if invoice.status not in Invoice.UNPAID_STATUSES or proof.amount > invoice.balance:
        raise ValidationError(
            {
                "amount": [
                    f"Only {invoice.balance} is owed on {invoice.reference} now. "
                    "Ask the tenant for details instead."
                ]
            }
        )
    proof.payment = record_payment(
        invoice=invoice,
        amount=proof.amount,
        method=proof.method,
        paid_on=proof.paid_on,
        reference=proof.reference,
        notes=f"Confirmed from payment proof {proof.number}",
        recorded_by=user,
    )
    proof.status = PaymentProof.Status.CONFIRMED
    proof.reviewed_by, proof.reviewed_at = user, timezone.now()
    proof.save(update_fields=["payment", "status", "reviewed_by", "reviewed_at", "updated_at"])
    # The receipt notice comes from the payment itself.
    return proof


@transaction.atomic
def decline(proof, *, user, note, ask=False):
    """Not received (final) or ask for details (the tenant can resend)."""
    proof = _locked(proof)
    if proof.status != PaymentProof.Status.SUBMITTED:
        raise ValidationError({"status": ["This payment is not waiting for review."]})
    if not note.strip():
        field = "Say what you need from the tenant." if ask else "Say why it was not received."
        raise ValidationError({"note": [field]})
    proof.status = (
        PaymentProof.Status.NEEDS_INFORMATION if ask else PaymentProof.Status.REJECTED
    )
    proof.review_note = note.strip()
    proof.reviewed_by, proof.reviewed_at = user, timezone.now()
    proof.save(update_fields=["status", "review_note", "reviewed_by", "reviewed_at", "updated_at"])
    _notify(
        proof,
        "proof.needs_information" if ask else "proof.rejected",
        tenant_only=True,
        state=proof.status,
        suffix=str(proof.revision),
        actor=user,
    )
    return proof


def matching_proofs(invoice):
    """Open proofs on an invoice, to warn before recording a payment by hand."""
    return invoice.payment_proofs.filter(status=PaymentProof.Status.SUBMITTED)
