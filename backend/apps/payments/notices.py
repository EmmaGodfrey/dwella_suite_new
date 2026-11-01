"""Payment-owned notice intents, called explicitly at locked status transitions.

Payment rows have no save hooks. Each caller captures the status it locked and
calls one of these inside the same transaction, after the row is saved, so the
intent commits or rolls back with the transition. Queuing failures are logged
and never undo a money movement (``safe_enqueue`` uses its own savepoint).
"""

from apps.notifications.events import safe_enqueue

# Tenants hear about attempts that did not take their money. A review can mean
# money was taken but not yet allocated, so only managers are told until it is
# resolved. A successful collection is announced by the billing receipt itself.
COLLECTION = {
    "failed": {"tenant_only": True},
    "expired": {"tenant_only": True},
    "review": {"managers_only": True},
}
PAYOUT = {"successful", "failed", "review"}
# "pending" is provider-side progress between queued and an outcome; skipping it
# keeps a normal withdrawal to two notices (requested, delivered).
WITHDRAWAL = {"queued", "cancelled", "successful", "failed", "review"}


def collection_changed(row, before):
    options = COLLECTION.get(row.status)
    if options and row.status != before:
        safe_enqueue(row, f"collection.{row.status}", state=row.status, **options)


def payout_changed(row, before):
    if row.status in PAYOUT and row.status != before:
        safe_enqueue(row, f"payout.{row.status}", state=row.status, managers_only=True)


def withdrawal_changed(row, before, actor=None):
    if row.status in WITHDRAWAL and row.status != before:
        safe_enqueue(
            row,
            f"withdrawal.{row.status}",
            state=row.status,
            managers_only=True,
            actor=actor,
        )
