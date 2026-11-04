"""Which approved WhatsApp template carries a money notice, and its body values.

Parameter order must match the wording submitted to Meta. Proof templates live in
``whatsapp/notices.py``, because they carry buttons and their own recipient rules.
"""

STATUS_WORDS = {
    "queued": "requested",
    "cancelled": "cancelled",
    "successful": "delivered",
    "failed": "failed",
    "review": "needs attention",
}


def _clean(values):
    # Meta refuses line breaks and runs of spaces inside template parameters.
    return [" ".join(str(value).split()) for value in values]


def money_template(row, target):
    """Return (template name, body values), or None when this notice has no template."""
    workspace = row.organization
    if row.event == "invoice.issued" and row.audience == "tenant":
        return "dwella_invoice_issued", _clean((
            target.tenant.full_name,
            workspace.name,
            target.reference,
            f"{workspace.currency} {target.total:,.2f}",
            f"{target.due_date:%d %b %Y}",
        ))
    # The wording addresses the person who paid, so managers do not receive this one.
    if row.event == "payment.confirmed" and row.audience == "tenant":
        return "dwella_payment_received", _clean((
            target.tenant.full_name,
            workspace.name,
            f"{workspace.currency} {target.amount:,.2f}",
            target.invoice.reference,
        ))
    kind, _, state = row.event.partition(".")
    if kind in {"payout", "withdrawal"} and row.audience == "manager" and state in STATUS_WORDS:
        return "dwella_payout_update", _clean((
            row.recipient_user.get_full_name() or "there",
            target.reference,
            f"{workspace.currency} {target.amount:,.2f}",
            STATUS_WORDS[state],
        ))
    return None


def covered_by_proof_notice(row):
    """A proof's own WhatsApp message already covers this notice, so do not repeat it."""
    from .whatsapp.models import WhatsAppProofNotice

    # Managers other than the chosen reviewer still get email and in-app notices.
    if row.event == "proof.submitted":
        return (
            WhatsAppProofNotice.objects.filter(proof_id=row.target_id, purpose="review")
            .exclude(status__in=["cancelled", "failed"])
            .exists()
        )
    if row.event != "payment.confirmed" or row.audience != "tenant":
        return False
    return (
        WhatsAppProofNotice.objects.filter(
            proof__payment_id=row.target_id,
            purpose="received",
            binding__user_id=row.recipient_user_id,
        )
        .exclude(status__in=["cancelled", "failed"])
        .exists()
    )
