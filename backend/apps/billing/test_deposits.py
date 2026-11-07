"""Security deposits: held for the tenant, separate from rent, never spent twice."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.leases.services import activate_lease, create_renewal
from apps.portal.tests import account, data

from . import deposits
from .models import DepositDeduction, DepositEntry, Invoice, InvoiceLine
from .services import create_invoice, record_payment, reverse_payment
from .tests import make_lease

pytestmark = pytest.mark.django_db
TODAY = timezone.localdate()
D = Decimal


@pytest.fixture
def home():
    from apps.organizations.models import Organization

    org = Organization.objects.create(name="Kafue Ridge Properties")
    lease = make_lease(org)
    lease.deposit_amount = D("3000")
    lease.save(update_fields=["deposit_amount"])
    manager_user, manager = account(org, "landlord", "deposit-manager")
    tenant_user, tenant = account(org, "tenant", "deposit-tenant")
    lease.tenant.user = tenant_user
    lease.tenant.email = tenant_user.email
    lease.tenant.save(update_fields=["user", "email"])
    return {
        "org": org,
        "lease": lease,
        "manager": manager,
        "manager_user": manager_user,
        "tenant": tenant,
    }


def url(lease, action=""):
    return f"/api/v1/billing/deposits/{lease.public_id}/{action}"


def pay(invoice, amount):
    return record_payment(invoice=invoice, amount=D(amount), method="cash", paid_on=TODAY)


def summary(lease):
    return deposits.summary(lease)


def test_requesting_the_deposit_issues_one_deposit_invoice(home):
    lease, manager = home["lease"], home["manager"]
    body = data(manager.post(url(lease, "request/"), {}, format="json"))
    assert body["requested_unpaid"] == "3000.00" and body["held"] == "0.00"
    invoice = Invoice.objects.get(lines__kind=InvoiceLine.Kind.DEPOSIT)
    assert invoice.total == D("3000") and invoice.period_start is None
    # Already invoiced: a second request would double-charge the tenant.
    assert manager.post(url(lease, "request/"), {}, format="json").status_code == 400


def test_payments_and_reversals_move_the_held_balance(home):
    lease = home["lease"]
    invoice = deposits.request_deposit(lease, user=home["manager_user"])
    pay(invoice, "1000")
    payment = pay(invoice, "2000")
    assert summary(lease)["held"] == D("3000")
    reverse_payment(payment, reason="Bounced transfer", user=home["manager_user"])
    info = summary(lease)
    assert info["held"] == D("1000")
    assert [e.amount for e in info["entries"]].count(D("-2000")) == 1
    # Top-up only asks for what is missing.
    assert deposits.requested_unpaid(lease) == D("2000")


def test_mixed_invoice_settles_rent_before_deposit(home):
    lease = home["lease"]
    invoice = create_invoice(
        organization=home["org"],
        tenant=lease.tenant,
        lease=lease,
        issue_date=TODAY,
        due_date=TODAY,
        lines=[
            {"kind": "rent", "description": "Rent", "amount": D("3900")},
            {"kind": "deposit", "description": "Deposit", "amount": D("3000")},
        ],
    )
    pay(invoice, "3900")
    assert summary(lease)["held"] == D("0")
    pay(invoice, "500")
    assert summary(lease)["held"] == D("500")


def test_deposit_already_held_before_dwella(home):
    lease, manager = home["lease"], home["manager"]
    body = data(
        manager.post(
            url(lease, "opening/"),
            {"amount": "3000", "occurred_on": str(TODAY - timedelta(days=200))},
            format="json",
        )
    )
    assert body["held"] == "3000.00" and not Invoice.objects.exists()
    future = {"amount": "10", "occurred_on": str(TODAY + timedelta(days=1))}
    assert manager.post(url(lease, "opening/"), future, format="json").status_code == 400


def test_deduction_reserves_until_applied_and_blocks_over_refunding(home):
    lease, manager, tenant = home["lease"], home["manager"], home["tenant"]
    deposits.record_opening(
        lease, amount=D("3000"), occurred_on=TODAY, note="", user=home["manager_user"]
    )
    too_much = {"amount": "3500", "reason": "Repaint"}
    assert manager.post(url(lease, "deductions/"), too_much, format="json").status_code == 400
    body = data(
        manager.post(
            url(lease, "deductions/"),
            {"amount": "400", "reason": "Replace broken bedroom door lock"},
            format="json",
        )
    )
    assert (body["held"], body["reserved"], body["available"]) == ("3000.00", "400.00", "2600.00")
    refund = {"amount": "2700", "method": "bank_transfer", "reference": "FT1"}
    assert manager.post(url(lease, "refunds/"), refund, format="json").status_code == 400
    deduction = DepositDeduction.objects.get()
    # Cannot apply before the tenant answers.
    apply_url = f"/api/v1/billing/deposit-deductions/{deduction.public_id}/apply/"
    assert manager.post(apply_url, {}, format="json").status_code == 400
    tenant_url = f"/api/v1/portal/deposit-deductions/{deduction.public_id}/respond/"
    assert tenant.post(tenant_url, {"decision": "accept"}, format="json").status_code == 200
    body = data(manager.post(apply_url, {}, format="json"))
    assert (body["held"], body["reserved"], body["available"]) == ("2600.00", "0.00", "2600.00")
    body = data(manager.post(url(lease, "refunds/"), {**refund, "amount": "2600"}, format="json"))
    assert body["held"] == "0.00"
    assert DepositEntry.objects.filter(kind="refund", amount=D("-2600")).exists()
    actions = set(AuditEvent.objects.values_list("action", flat=True))
    assert {
        "deposit.deduction_proposed",
        "deposit.deduction_accepted",
        "deposit.deduction_applied",
        "deposit.refund_recorded",
    } <= actions


def test_disputed_deduction_needs_a_resolution_and_can_be_withdrawn(home):
    lease, manager, tenant = home["lease"], home["manager"], home["tenant"]
    deposits.record_opening(
        lease, amount=D("1000"), occurred_on=TODAY, note="", user=home["manager_user"]
    )
    row = deposits.propose_deduction(
        lease, amount=D("300"), reason="Carpet cleaning", details="", user=home["manager_user"]
    )
    respond = f"/api/v1/portal/deposit-deductions/{row.public_id}/respond/"
    # A dispute must say why.
    assert tenant.post(respond, {"decision": "dispute"}, format="json").status_code == 400
    tenant.post(respond, {"decision": "dispute", "note": "Fair wear and tear"}, format="json")
    apply_url = f"/api/v1/billing/deposit-deductions/{row.public_id}/apply/"
    assert manager.post(apply_url, {}, format="json").status_code == 400
    withdraw = f"/api/v1/billing/deposit-deductions/{row.public_id}/withdraw/"
    body = data(manager.post(withdraw, {}, format="json"))
    assert body["available"] == "1000.00"
    # Tenants no longer see a withdrawn proposal.
    portal = data(tenant.get("/api/v1/portal/deposits/"))
    assert portal[0]["deductions"] == [] and portal[0]["held"] == "1000.00"


def test_tenants_only_see_and_answer_their_own(home):
    org, manager_user = home["org"], home["manager_user"]
    neighbour = make_lease(org, unit_name="2B", phone="+260975550000")
    deposits.record_opening(
        neighbour, amount=D("500"), occurred_on=TODAY, note="", user=manager_user
    )
    theirs = deposits.propose_deduction(
        neighbour, amount=D("100"), reason="Keys", details="", user=manager_user
    )
    tenant = home["tenant"]
    leases = [row["lease"]["reference"] for row in data(tenant.get("/api/v1/portal/deposits/"))]
    assert leases == [home["lease"].reference]
    respond = f"/api/v1/portal/deposit-deductions/{theirs.public_id}/respond/"
    assert tenant.post(respond, {"decision": "accept"}, format="json").status_code == 404
    assert tenant.get(url(home["lease"])).status_code == 403


def test_renewal_carries_the_unreserved_deposit_over(home):
    lease, manager_user = home["lease"], home["manager_user"]
    lease.end_date = TODAY - timedelta(days=1)
    lease.save(update_fields=["end_date"])
    deposits.record_opening(lease, amount=D("3000"), occurred_on=TODAY, note="", user=manager_user)
    deposits.propose_deduction(
        lease, amount=D("200"), reason="Broken window", details="", user=manager_user
    )
    renewal = create_renewal(lease, end_date=TODAY + timedelta(days=365))
    activate_lease(renewal)
    assert summary(renewal)["held"] == D("2800")
    old = summary(lease)
    assert (old["held"], old["reserved"]) == (D("200"), D("200"))
    # Top-up asks only for the difference against the new agreement.
    renewal.deposit_amount = D("3300")
    renewal.save(update_fields=["deposit_amount"])
    invoice = deposits.request_deposit(renewal, user=manager_user)
    assert invoice.total == D("500")
    assert "top-up" in invoice.lines.get().description
