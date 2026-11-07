"""Existing tenancies: old debt, rent paid ahead and deposits, without new billing."""

from datetime import timedelta
from decimal import Decimal as D

import pytest
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.integrations.models import FiscalReceipt
from apps.leases.services import end_lease
from apps.notifications.models import OperationalDelivery
from apps.notifications.operational import schedule_operational
from apps.organizations.models import Organization
from apps.portal.tests import account, data

from . import opening
from .models import DepositEntry, Invoice
from .services import (
    apply_late_fees,
    create_invoice,
    first_of_month,
    generate_rent_invoices,
    issue_upcoming_rent,
    record_payment,
    void_invoice,
)
from .tests import make_lease

pytestmark = pytest.mark.django_db
URL = "/api/v1/billing/opening-balances/"
TODAY = timezone.localdate()
THIS_MONTH = first_of_month(TODAY)
NEXT_MONTH = first_of_month(THIS_MONTH + timedelta(days=32))
LONG_AGO = TODAY - timedelta(days=75)


@pytest.fixture
def home():
    org = Organization.objects.create(name="Kafue Ridge Properties")
    lease = make_lease(org)
    user, manager = account(org, "landlord", "opening-manager")
    return {"org": org, "lease": lease, "manager": manager, "user": user}


def save(home, *rows, **body):
    return home["manager"].post(URL, {"rows": list(rows), **body}, format="json")


def row(lease, **fields):
    return {"lease": str(lease.public_id), **fields}


def opening_invoice(lease):
    return Invoice.objects.get(lease=lease, is_opening_balance=True)


def test_old_debt_is_one_payable_invoice_dated_when_it_fell_due(home):
    lease = home["lease"]
    response = save(home, row(lease, owes="2500.00", owed_since=str(LONG_AGO)))
    assert response.status_code == 200, response.content
    invoice = opening_invoice(lease)
    assert invoice.total == D("2500") and invoice.period_start is None
    assert invoice.issue_date == invoice.due_date == LONG_AGO
    assert invoice.lines.get().description == "Balance brought forward"
    assert AuditEvent.objects.filter(action="billing.opening_balance_recorded").exists()
    record_payment(invoice=invoice, amount=D("500"), method="cash", paid_on=TODAY)
    invoice.refresh_from_db()
    assert invoice.status == "partially_paid" and invoice.balance == D("2000")


def test_old_debt_defaults_to_the_as_of_date(home):
    lease = home["lease"]
    as_of = str(TODAY - timedelta(days=3))
    assert save(home, row(lease, owes="100.00"), as_of=as_of).status_code == 200
    assert str(opening_invoice(lease).due_date) == as_of


def test_old_debt_sends_nothing_and_charges_no_late_fee(home):
    lease = home["lease"]
    org = home["org"]
    tenant_user, _ = account(org, "tenant", "opening-tenant")
    lease.tenant.user = tenant_user
    lease.tenant.email = tenant_user.email
    lease.tenant.save(update_fields=["user", "email"])
    OperationalDelivery.objects.all().delete()
    # Overdue by exactly a reminder date, on a lease that charges late fees.
    invoice = opening.record_opening_balance(
        lease, amount=D("900"), owed_since=TODAY - timedelta(days=3)
    )
    # An ordinary invoice with the same dates, proving notices would have gone.
    ordinary = create_invoice(
        organization=org,
        tenant=lease.tenant,
        lease=lease,
        issue_date=TODAY - timedelta(days=3),
        due_date=TODAY - timedelta(days=3),
        lines=[{"kind": "other", "description": "Water", "amount": D("50")}],
    )
    schedule_operational(now=timezone.localtime().replace(hour=12))
    events = set(OperationalDelivery.objects.values_list("event", "target_id"))
    assert ("invoice.issued", ordinary.pk) in events
    assert ("invoice.reminder", ordinary.pk) in events
    assert not [row for row in events if row[1] == invoice.pk]
    assert apply_late_fees(org, today=TODAY) == 0
    invoice.refresh_from_db()
    assert invoice.total == D("900")
    assert not FiscalReceipt.objects.filter(invoice=invoice).exists()
    void_invoice(invoice)
    assert not OperationalDelivery.objects.filter(event="invoice.void").exists()


def test_old_debt_counts_as_owed_but_not_as_billed_this_month(home):
    opening.record_opening_balance(home["lease"], amount=D("900"), owed_since=TODAY)
    body = data(home["manager"].get("/api/v1/billing/invoices/summary/"))
    assert body["outstanding"] == "900.00"
    assert body["billed_this_month"] == "0.00" and body["invoices_this_month"] == 0
    assert body["month_breakdown"]["billed"] == "0.00"
    assert all(month["billed"] in ("0.00", 0, None) for month in body["history"])


def test_a_lease_has_one_live_opening_balance_until_it_is_voided(home):
    lease = home["lease"]
    invoice = opening.record_opening_balance(lease, amount=D("900"), owed_since=TODAY)
    again = save(home, row(lease, owes="100.00"))
    assert again.status_code == 400 and invoice.reference in str(again.content)
    with pytest.raises(IntegrityError), transaction.atomic():
        create_invoice(
            organization=home["org"],
            tenant=lease.tenant,
            lease=lease,
            issue_date=TODAY,
            due_date=TODAY,
            is_opening_balance=True,
            lines=[{"kind": "other", "description": "Second", "amount": D("1")}],
        )
    void_invoice(invoice)
    assert save(home, row(lease, owes="800.00")).status_code == 200
    assert opening.live_opening_balance(lease).total == D("800")


def test_rent_paid_ahead_is_not_billed_until_the_next_month(home):
    lease, org = home["lease"], home["org"]
    assert save(home, row(lease, rent_paid_up_to=str(THIS_MONTH))).status_code == 200
    lease.refresh_from_db()
    assert lease.billed_from == NEXT_MONTH
    assert opening.rent_paid_up_to(lease) == THIS_MONTH
    generate_rent_invoices(org, THIS_MONTH)
    assert not Invoice.objects.filter(lease=lease, period_start=THIS_MONTH).exists()
    generate_rent_invoices(org, NEXT_MONTH)
    assert Invoice.objects.filter(lease=lease, period_start=NEXT_MONTH).exists()
    # Automatic billing follows the same rule.
    Invoice.objects.filter(lease=lease).delete()
    org.invoice_lead_days = 28
    org.save(update_fields=["invoice_lead_days"])
    issue_upcoming_rent(org, today=TODAY)
    assert not Invoice.objects.filter(lease=lease, period_start=THIS_MONTH).exists()


def test_rent_paid_up_to_can_be_cleared(home):
    lease = home["lease"]
    save(home, row(lease, rent_paid_up_to=str(THIS_MONTH)))
    assert save(home, row(lease, rent_paid_up_to=None)).status_code == 200
    lease.refresh_from_db()
    assert lease.billed_from is None


def test_rent_paid_up_to_rejects_past_and_past_the_lease(home):
    lease = home["lease"]
    past = THIS_MONTH - timedelta(days=1)
    assert save(home, row(lease, rent_paid_up_to=str(past))).status_code == 400
    late = lease.end_date + timedelta(days=40)
    assert save(home, row(lease, rent_paid_up_to=str(late))).status_code == 400


def test_an_unpaid_rent_invoice_must_be_voided_before_marking_it_paid_ahead(home):
    lease = home["lease"]
    generate_rent_invoices(home["org"], THIS_MONTH)
    invoice = Invoice.objects.get(lease=lease, period_start=THIS_MONTH)
    blocked = save(home, row(lease, rent_paid_up_to=str(THIS_MONTH)))
    assert blocked.status_code == 400 and invoice.reference in str(blocked.content)
    void_invoice(invoice)
    assert save(home, row(lease, rent_paid_up_to=str(THIS_MONTH))).status_code == 200


def test_deposit_already_held_issues_no_receipt_and_is_recorded_once(home):
    lease = home["lease"]
    as_of = str(TODAY - timedelta(days=1))
    assert save(home, row(lease, deposit_held="3000.00"), as_of=as_of).status_code == 200
    entry = DepositEntry.objects.get(lease=lease)
    assert entry.kind == "opening" and entry.amount == D("3000") and str(entry.occurred_on) == as_of
    assert not Invoice.objects.filter(lease=lease).exists()
    assert save(home, row(lease, deposit_held="1.00")).status_code == 400
    assert DepositEntry.objects.filter(lease=lease).count() == 1


def test_a_bad_row_saves_nothing_and_names_the_row(home):
    good, bad = home["lease"], make_lease(home["org"], unit_name="2B", phone="+260975550000")
    response = save(
        home,
        row(good, owes="100.00", deposit_held="50.00"),
        row(bad, owes="-5.00"),
    )
    assert response.status_code == 400
    assert not Invoice.objects.filter(is_opening_balance=True).exists()
    assert not DepositEntry.objects.exists()


@pytest.mark.parametrize("body", [
    {"rows": []},
    {"rows": [{"lease": "not-a-uuid"}]},
])
def test_malformed_batches_are_rejected(home, body):
    assert home["manager"].post(URL, body, format="json").status_code == 400


def test_batches_are_bounded_and_future_dates_rejected(home):
    lease = home["lease"]
    repeated = [row(lease, owes="1.00") for _ in range(2)]
    assert save(home, *repeated).status_code == 400
    tomorrow = str(TODAY + timedelta(days=1))
    assert save(home, row(lease, owes="1.00"), as_of=tomorrow).status_code == 400
    assert save(home, row(lease, owes="1.00", owed_since=tomorrow)).status_code == 400
    assert not Invoice.objects.filter(is_opening_balance=True).exists()


def test_only_active_leases_in_this_workspace_can_be_changed(home):
    ended = home["lease"]
    end_lease(ended)
    assert save(home, row(ended, owes="1.00")).status_code == 400
    draft = make_lease(home["org"], unit_name="2C", phone="+260975550001", active=False)
    assert save(home, row(draft, owes="1.00")).status_code == 400
    other = Organization.objects.create(name="Another workspace")
    theirs = make_lease(other, unit_name="9Z", phone="+260975550002")
    assert save(home, row(theirs, owes="1.00")).status_code == 400
    assert not Invoice.objects.filter(is_opening_balance=True).exists()


def test_tenants_cannot_use_it(home):
    _, tenant = account(home["org"], "tenant", "opening-tenant")
    assert tenant.get(URL).status_code == 403
    response = tenant.post(URL, {"rows": [row(home["lease"], owes="1.00")]}, format="json")
    assert response.status_code == 403


def test_the_list_shows_what_is_recorded_and_what_is_still_waiting(home):
    done, waiting = home["lease"], make_lease(home["org"], unit_name="2B", phone="+260975550000")
    invoice = opening.record_opening_balance(done, amount=D("900"), owed_since=LONG_AGO)
    opening.record_deposit_held(done, amount=D("3000"), occurred_on=TODAY, user=home["user"])
    opening.set_rent_paid_up_to(done, THIS_MONTH)
    rows = {r["lease"]: r for r in data(home["manager"].get(URL))}
    recorded = rows[str(done.public_id)]
    assert recorded["opening_balance"]["reference"] == invoice.reference
    assert recorded["opening_balance"]["balance"] == "900.00"
    assert recorded["deposit_held"] == "3000.00"
    assert recorded["rent_paid_up_to"] == THIS_MONTH.isoformat()
    untouched = rows[str(waiting.public_id)]
    assert untouched["opening_balance"] is None and untouched["rent_paid_up_to"] is None
    pending = data(home["manager"].get(URL, {"pending": "true"}))
    assert [r["lease"] for r in pending] == [str(waiting.public_id)]
    found = data(home["manager"].get(URL, {"search": "2B"}))
    assert [r["lease"] for r in found] == [str(waiting.public_id)]


def test_list_queries_stay_flat_and_saving_a_full_page_is_bounded(home):
    def read():
        with CaptureQueriesContext(connection) as queries:
            assert home["manager"].get(URL).status_code == 200
        return len(queries)

    few = read()
    leases = [
        make_lease(home["org"], unit_name=f"U{n}", phone=f"+2609755510{n:02d}") for n in range(24)
    ]
    for lease in leases[:12]:
        opening.record_opening_balance(lease, amount=D("10"), owed_since=TODAY)
    assert read() == few
    rows = [row(lease, deposit_held="10.00") for lease in leases[12:]]
    with CaptureQueriesContext(connection) as queries:
        assert save(home, *rows).status_code == 200
    # Twelve rows: about a dozen trips each, never a scan of the whole workspace.
    assert len(queries) <= 25 + 12 * 12, len(queries)
