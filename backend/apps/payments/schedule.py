"""When the worker asks Lenco about a collection or payout again.

Checks start quickly, slow down as a row ages, and stop once nothing can
change. A webhook only brings the next check forward. Because a repeated
identical answer is not stored again, a quiet row costs one indexed read
and one small update per check.
"""

from datetime import timedelta

from django.utils.dateparse import parse_datetime

from .models import Collection, Payout

# A checkout not paid within this window expires and frees the invoice.
CHECKOUT_WINDOW = timedelta(minutes=30)
# A submitted payout Lenco has not confirmed by then needs a person.
PAYOUT_CONFIRMATION_LIMIT = timedelta(days=3)
SETTLEMENT_OVERDUE = timedelta(days=7)


def stamp(value):
    return value.isoformat() if value else None


def parse_stamp(value):
    parsed = parse_datetime(value) if isinstance(value, str) else None
    return parsed if parsed and parsed.tzinfo else None


def checkout_started(row):
    """The later of creation and the last webhook: a webhook extends the window."""
    webhook = parse_stamp((row.provider_state or {}).get("webhook_at"))
    return max(row.created_at, webhook) if webhook else row.created_at


def checkout_window_over(row, now):
    return now - checkout_started(row) >= CHECKOUT_WINDOW


def collection_next_check(row, now):
    if row.status == Collection.Status.FAILED:
        # Only a webhook reopens a failed checkout, and only for a while.
        webhook = parse_stamp((row.provider_state or {}).get("webhook_at"))
        if webhook and now - webhook < CHECKOUT_WINDOW:
            return now + timedelta(minutes=2)
        return None
    if row.status == Collection.Status.EXPIRED:
        # Mobile money can be approved late. Keep a slow safety net in case
        # Lenco's webhook for that late approval never arrives.
        age = now - checkout_started(row)
        if age < CHECKOUT_WINDOW:  # revived by a webhook
            return now + timedelta(minutes=2)
        if age < CHECKOUT_WINDOW + timedelta(hours=2):
            return now + timedelta(minutes=15)
        if age < timedelta(days=1):
            return now + timedelta(hours=2)
        return None
    if row.status == Collection.Status.PENDING:
        age = now - checkout_started(row)
        if age < timedelta(minutes=5):
            return now + timedelta(seconds=30)
        if age < CHECKOUT_WINDOW:
            return now + timedelta(minutes=2)
        # Still unknown after the window (Lenco unreachable): keep asking, slowly.
        return now + timedelta(minutes=15)
    if row.status == Collection.Status.SUCCESSFUL and not row.settled:
        age = now - row.created_at
        if age < timedelta(hours=1):
            return now + timedelta(minutes=5)
        if age < timedelta(days=2):
            return now + timedelta(minutes=30)
        return now + timedelta(hours=2)
    return None


def payout_next_check(row, now):
    if row.status == Payout.Status.QUEUED:
        return now
    if row.status in (Payout.Status.SUBMITTING, Payout.Status.PENDING):
        age = now - (row.submitted_at or row.created_at)
        if age < timedelta(minutes=5):
            return now + timedelta(seconds=30)
        if age < timedelta(hours=1):
            return now + timedelta(minutes=2)
        return now + timedelta(minutes=15)
    return None
