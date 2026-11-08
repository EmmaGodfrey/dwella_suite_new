from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.organizations.models import OrganizationMembership

from .models import PayoutPlan, Withdrawal
from .payout_plans import next_slot, run_due_plans, save_plan
from .services import reconcile_collection
from .testing import checkout, client_for, collection_result, paid

pytestmark = pytest.mark.django_db
D = Decimal


@pytest.fixture(autouse=True)
def manual(settings):
    settings.LENCO_AUTOMATIC_PAYOUTS = False


def at(*args):
    return timezone.make_aware(datetime(*args))


def paid_again(home):
    row = checkout(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(
            row, id="provider-collection-2"
        )
        reconcile_collection(row)


def plan(timing, **kwargs):
    return PayoutPlan(timing=timing, **kwargs)


def test_weekly_and_monthly_slots_are_the_next_08_00_in_lusaka():
    monday = plan("weekly", weekday=0)
    # Wednesday 11 Nov 2026.
    assert next_slot(monday, at(2026, 11, 11, 10)) == at(2026, 11, 16, 8)
    assert next_slot(monday, at(2026, 11, 16, 7, 59)) == at(2026, 11, 16, 8)
    assert next_slot(monday, at(2026, 11, 16, 8)) == at(2026, 11, 23, 8)
    last = plan("monthly", month_day=0)
    assert next_slot(last, at(2026, 11, 10)) == at(2026, 11, 30, 8)
    assert next_slot(last, at(2026, 11, 30, 9)) == at(2026, 12, 31, 8)
    assert next_slot(last, at(2026, 12, 31, 9)) == at(2027, 1, 31, 8)
    assert next_slot(last, at(2027, 1, 31, 9)) == at(2027, 2, 28, 8)
    assert next_slot(plan("monthly", month_day=15), at(2026, 11, 10)) == at(2026, 11, 15, 8)
    assert next_slot(plan("manual"), at(2026, 11, 10)) is None


def test_saving_a_timing_never_sends_a_slot_that_already_passed(home):
    saved = save_plan(
        organization=home["org"],
        user=home["manager"],
        timing="weekly",
        weekday=0,
        now=at(2026, 11, 16, 9),
    )
    assert saved.next_run_at == at(2026, 11, 23, 8)


def test_a_due_weekly_timing_sends_the_largest_amount_once_per_slot(home):
    paid(home)  # K97.50 settled
    saved = save_plan(organization=home["org"], user=home["manager"], timing="weekly")
    slot = saved.next_run_at
    assert run_due_plans(slot) == 1
    row = Withdrawal.objects.get()
    assert row.automatic and row.requested_by == home["manager"]
    # The amount plus the K12 reserve uses the whole balance.
    assert row.amount == D("85.50") and row.fee_reserved == D("12.00")
    saved.refresh_from_db()
    assert saved.next_run_at > slot
    # Running the same slot again, even if the plan were rewound, sends nothing new.
    PayoutPlan.objects.filter(pk=saved.pk).update(next_run_at=slot)
    run_due_plans(slot)
    assert Withdrawal.objects.count() == 1


def test_as_funds_settle_waits_while_a_withdrawal_is_processing(home):
    paid(home)
    save_plan(organization=home["org"], user=home["manager"], timing="settled")
    now = timezone.now()
    assert run_due_plans(now) == 1
    paid_again(home)
    PayoutPlan.objects.update(next_run_at=now)
    assert run_due_plans(now) == 0
    Withdrawal.objects.update(status="successful", fee_charged=D("8.50"))
    PayoutPlan.objects.update(next_run_at=now)
    assert run_due_plans(now) == 1
    assert Withdrawal.objects.count() == 2


def test_nothing_is_sent_below_the_minimum_or_for_a_former_manager(home):
    save_plan(organization=home["org"], user=home["manager"], timing="settled")
    now = timezone.now()
    assert run_due_plans(now) == 0  # no settled rent yet
    paid(home)
    OrganizationMembership.objects.filter(user=home["manager"]).update(is_active=False)
    PayoutPlan.objects.update(next_run_at=now)
    assert run_due_plans(now) == 0
    assert not Withdrawal.objects.exists()


def test_timings_wait_while_withdrawals_are_switched_off(home, settings):
    paid(home)
    save_plan(organization=home["org"], user=home["manager"], timing="settled")
    settings.LENCO_PAYOUTS_ENABLED = False
    assert run_due_plans(timezone.now()) == 0


def test_manager_reads_and_changes_payout_timing(home):
    client = client_for(home["manager"])
    assert client.get("/api/v1/payments/payouts/timing/").data["timing"] == "manual"
    response = client.put(
        "/api/v1/payments/payouts/timing/", {"timing": "monthly", "month_day": 0}, format="json"
    )
    assert response.status_code == 200, response.data
    assert response.data["timing"] == "monthly" and response.data["next_run_at"]
    stored = PayoutPlan.objects.get()
    assert stored.set_by == home["manager"] and stored.organization == home["org"]
    bad = client.put("/api/v1/payments/payouts/timing/", {"timing": "weekly", "weekday": 7})
    assert bad.status_code == 400


def test_only_the_property_manager_changes_payout_timing(home):
    body = {"timing": "weekly", "weekday": 0}
    url = "/api/v1/payments/payouts/timing/"
    assert client_for(home["tenant"]).put(url, body, format="json").status_code == 403
    assert client_for(home["admin"]).put(url, body, format="json").status_code == 403
    home["destination"].enabled = False
    home["destination"].save(update_fields=["enabled"])
    refused = client_for(home["manager"]).put(url, body, format="json")
    assert refused.status_code == 400 and "receiving account" in str(refused.data)
    assert not PayoutPlan.objects.exists()
