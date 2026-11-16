"""Payout timing: send settled rent weekly, monthly or as it settles.

A due plan becomes one ordinary withdrawal of the largest amount the balance
allows after its fee, requested for the manager who chose the timing. The
withdrawal path then applies every guard a manual request gets: the workspace
lock, the fee reserve, a fresh matched Lenco balance and a single send.
Weekly and monthly runs use one idempotency key per slot, so a slot can never
send twice; "as funds settle" waits while a withdrawal is still processing.
"""

import calendar
import logging
import uuid
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import PayoutPlan, Withdrawal
from .withdrawals import (
    HOLDING,
    balance,
    current_destination,
    fee_for,
    is_landlord,
    largest_withdrawal,
    request_withdrawal,
    withdrawals_enabled,
)

RUN_AT = time(8, 0)
# Settlement is seen by the balance sync, which runs every five minutes.
SETTLED_EVERY = timedelta(minutes=5)
logger = logging.getLogger(__name__)


def _at(day):
    return timezone.make_aware(datetime.combine(day, RUN_AT))


def _month_slot(plan, year, month):
    last = calendar.monthrange(year, month)[1]
    return _at(date(year, month, plan.month_day or last))


def next_slot(plan, now):
    """The first run strictly after `now`, or None when payouts are held."""
    if plan.timing == PayoutPlan.Timing.SETTLED:
        return now + SETTLED_EVERY
    local = timezone.localtime(now).date()
    if plan.timing == PayoutPlan.Timing.WEEKLY:
        slot = _at(local + timedelta(days=(plan.weekday - local.weekday()) % 7))
        return slot if slot > now else slot + timedelta(days=7)
    if plan.timing == PayoutPlan.Timing.MONTHLY:
        slot = _month_slot(plan, local.year, local.month)
        if slot > now:
            return slot
        year, month = (local.year + 1, 1) if local.month == 12 else (local.year, local.month + 1)
        return _month_slot(plan, year, month)
    return None


def save_plan(*, organization, user, timing, weekday=0, month_day=0, now=None):
    """Call inside the workspace lock. The first run is the next slot, never a missed one."""
    now = now or timezone.now()
    plan = PayoutPlan.objects.filter(organization=organization).first() or PayoutPlan(
        organization=organization
    )
    plan.timing, plan.weekday, plan.month_day, plan.set_by = timing, weekday, month_day, user
    plan.next_run_at = now if timing == PayoutPlan.Timing.SETTLED else next_slot(plan, now)
    plan.save()
    return plan


def run_due_plans(now=None, limit=20):
    """Start the withdrawals of every due plan; one plan's failure never stops another."""
    if not withdrawals_enabled():
        return 0
    now = now or timezone.now()
    due = list(
        PayoutPlan.objects.filter(next_run_at__lte=now)
        .exclude(timing=PayoutPlan.Timing.MANUAL)
        .order_by("next_run_at")
        .values_list("pk", flat=True)[:limit]
    )
    started = 0
    for pk in due:
        try:
            started += run_plan(pk, now) is not None
        except Exception:
            logger.exception("Payout timing failed for plan %s", pk)
    return started


def run_plan(pk, now):
    # Move the plan on first, so a failed run waits for its next slot.
    with transaction.atomic():
        plan = (
            PayoutPlan.objects.select_for_update()
            .filter(pk=pk, next_run_at__lte=now)
            .exclude(timing=PayoutPlan.Timing.MANUAL)
            .first()
        )
        if plan is None:
            return None
        slot = plan.next_run_at
        plan.next_run_at = next_slot(plan, now)
        plan.save(update_fields=["next_run_at", "updated_at"])
    return _send(plan, slot)


def _send(plan, slot):
    organization = plan.organization
    destination = current_destination(organization)
    if destination is None or not is_landlord(plan.set_by, organization):
        return None
    settled = plan.timing == PayoutPlan.Timing.SETTLED
    if (
        settled
        and Withdrawal.objects.filter(organization=organization, status__in=HOLDING).exists()
    ):
        return None
    amount = largest_withdrawal(destination.kind, balance(organization)["available"])
    if amount is None:
        return None
    key = uuid.uuid4() if settled else uuid.uuid5(plan.public_id, slot.isoformat())
    try:
        return request_withdrawal(
            organization=organization,
            user=plan.set_by,
            amount=amount,
            fee=fee_for(destination.kind, amount),
            idempotency_key=key,
            automatic=True,
        )
    except ValidationError:
        # The balance moved since it was read; the next slot tries again.
        return None
