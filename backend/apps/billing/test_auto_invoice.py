# ruff: noqa: F811  (org/manager fixtures are imported from .tests)
"""Automatic rent invoices go out a set number of days before each due day."""

from datetime import timedelta
from unittest import mock

import pytest
from django.core.management import call_command

from .models import Invoice
from .services import issue_upcoming_rent
from .tests import THIS_MONTH, make_lease, manager, org  # noqa: F401  (shared fixtures)

M = THIS_MONTH  # leases from make_lease run around the current month
N = (M + timedelta(days=32)).replace(day=1)


def day(n):
    return M.replace(day=n)


pytestmark = pytest.mark.django_db


def due_on(lease, day):
    lease.rent_due_day = day
    lease.save(update_fields=["rent_due_day"])
    return lease


def periods(org):
    return sorted(
        (i.period_start, i.issue_date, i.due_date) for i in Invoice.objects.filter(organization=org)
    )


def test_next_month_goes_out_seven_days_before_it_is_due(org):
    due_on(make_lease(org), 5)
    next_due = N.replace(day=5)
    send_on = next_due - timedelta(days=7)
    # Mid-month: this month (due the 5th) is caught up; next month is not close yet.
    assert issue_upcoming_rent(org, day(20)) == 1
    assert issue_upcoming_rent(org, send_on - timedelta(days=1)) == 0
    assert issue_upcoming_rent(org, send_on) == 1
    assert periods(org) == [(M, day(20), day(20)), (N, send_on, next_due)]
    # Running again the same day or later never bills a month twice.
    assert issue_upcoming_rent(org, next_due) == 0


def test_lead_time_is_the_workspaces_choice(org):
    org.invoice_lead_days = 0
    org.save(update_fields=["invoice_lead_days"])
    due_on(make_lease(org), 10)
    assert issue_upcoming_rent(org, day(9)) == 0
    assert issue_upcoming_rent(org, day(10)) == 1
    assert Invoice.objects.get().due_date == day(10)


def test_due_on_the_first_bills_the_previous_month(org):
    make_lease(org)
    # Seven days before the 1st of next month; this month is already due.
    issue_upcoming_rent(org, N - timedelta(days=7))
    assert [p for p, _, _ in periods(org)] == [M, N]


def test_lease_that_has_ended_is_not_billed_ahead(org):
    lease = make_lease(org)
    lease.end_date = N - timedelta(days=1)
    lease.save(update_fields=["end_date"])
    issue_upcoming_rent(org, N - timedelta(days=3))
    assert [p for p, _, _ in periods(org)] == [M]


def test_workspace_with_automatic_invoices_off_is_skipped(org):
    org.auto_invoice = False
    org.save(update_fields=["auto_invoice"])
    make_lease(org)
    with mock.patch("apps.billing.management.commands.run_billing.apply_late_fees") as fees:
        fees.return_value = 0
        call_command("run_billing")
    assert not Invoice.objects.exists()
    # Late fees on invoices issued by hand still apply.
    fees.assert_called_once()


def test_manager_sets_automatic_invoices_in_workspace_settings(manager, org):
    url = "/api/v1/notifications/workspace-settings/"
    data = manager.get(url).json()["response_data"]
    assert data["auto_invoice"] is True and data["invoice_lead_days"] == 7
    reply = manager.patch(url, {"auto_invoice": False, "invoice_lead_days": 3}, format="json")
    assert reply.status_code == 200
    org.refresh_from_db()
    assert (org.auto_invoice, org.invoice_lead_days) == (False, 3)
    too_far = manager.patch(url, {"invoice_lead_days": 29}, format="json")
    assert too_far.status_code == 400
