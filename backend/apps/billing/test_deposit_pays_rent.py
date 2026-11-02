"""A deduction can pay unpaid rent from the deposit, with a normal receipt."""

# ruff: noqa: F811
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.portal.tests import data

from . import deposits
from .models import DepositDeduction, DepositEntry, Invoice, Payment
from .services import create_invoice, reverse_payment
from .test_deposits import home, url  # noqa: F401  (shared fixture)

pytestmark = pytest.mark.django_db
TODAY = timezone.localdate()
D = Decimal


def held_deposit(home, amount="3000"):
    deposits.record_opening(
        home["lease"], amount=D(amount), occurred_on=TODAY, note="", user=home["manager_user"]
    )


def rent(home, amount="3900"):
    lease = home["lease"]
    return create_invoice(
        organization=home["org"],
        tenant=lease.tenant,
        lease=lease,
        issue_date=TODAY,
        due_date=TODAY,
        lines=[{"kind": "rent", "description": "Rent", "amount": D(amount)}],
    )


def propose(home, invoice, amount):
    return home["manager"].post(
        url(home["lease"], "deductions/"),
        {"amount": amount, "reason": "Unpaid November rent", "invoice": str(invoice.public_id)},
        format="json",
    )


def deduction_for(response):
    return DepositDeduction.objects.get(public_id=data(response)["created_id"])


def test_applied_deduction_pays_the_invoice_with_a_receipt(home):
    held_deposit(home)
    invoice = rent(home)
    body = data(home["manager"].get(url(home["lease"])))
    assert [row["reference"] for row in body["payable_invoices"]] == [invoice.reference]
    row = deduction_for(propose(home, invoice, "2500"))
    deposits.respond_to_deduction(row, accept=True, note="")
    response = home["manager"].post(f"/api/v1/billing/deposit-deductions/{row.public_id}/apply/")
    assert response.status_code == 200, response.content
    invoice.refresh_from_db()
    row.refresh_from_db()
    assert invoice.amount_paid == D("2500") and invoice.status == Invoice.Status.PARTIALLY_PAID
    assert row.payment.method == Payment.Method.DEPOSIT
    assert row.payment.recorded_by == home["manager_user"]
    assert deposits.held(home["lease"]) == D("500")
    applied = data(response)["deductions"][0]
    assert applied["invoice"]["reference"] == invoice.reference
    assert applied["receipt"]["number"] == row.payment.receipt_number
    # The tenant sees the same link to their invoice and receipt.
    tenant = data(home["tenant"].get("/api/v1/portal/deposits/"))[0]["deductions"][0]
    assert tenant["receipt"]["number"] == row.payment.receipt_number
    assert "payable_invoices" not in data(home["tenant"].get("/api/v1/portal/deposits/"))[0]


def test_deduction_cannot_pay_more_than_is_owed(home):
    held_deposit(home)
    invoice = rent(home, "1000")
    assert propose(home, invoice, "1500").status_code == 400
    row = deduction_for(propose(home, invoice, "800"))
    deposits.respond_to_deduction(row, accept=True, note="")
    # The tenant paid part of it meanwhile; applying now would overpay the invoice.
    from .services import record_payment

    record_payment(invoice=invoice, amount=D("500"), method="cash", paid_on=TODAY)
    with pytest.raises(Exception) as error:
        deposits.apply_deduction(row, user=home["manager_user"])
    assert "Only 500.00 is owed" in str(error.value.detail)
    assert deposits.held(home["lease"]) == D("3000")


def test_deposit_invoices_and_other_leases_cannot_be_paid_from_the_deposit(home):
    held_deposit(home)
    lease = home["lease"]
    lease.deposit_amount = D("5000")
    lease.save(update_fields=["deposit_amount"])
    deposit_invoice = deposits.request_deposit(lease, user=home["manager_user"])
    assert propose(home, deposit_invoice, "100").status_code == 400
    from .tests import make_lease

    other = make_lease(home["org"], unit_name="3B", phone="+260974123382")
    stranger = create_invoice(
        organization=home["org"],
        tenant=other.tenant,
        lease=other,
        issue_date=TODAY,
        due_date=TODAY,
        lines=[{"kind": "rent", "description": "Rent", "amount": D("1000")}],
    )
    assert propose(home, stranger, "100").status_code == 400


def test_reversing_the_deposit_payment_returns_the_money(home):
    held_deposit(home)
    invoice = rent(home)
    row = deduction_for(propose(home, invoice, "3000"))
    deposits.respond_to_deduction(row, accept=True, note="")
    deposits.apply_deduction(row, user=home["manager_user"])
    row.refresh_from_db()
    assert deposits.held(home["lease"]) == D("0")
    reverse_payment(row.payment, reason="Wrong month", user=home["manager_user"])
    row.refresh_from_db()
    invoice.refresh_from_db()
    assert invoice.amount_paid == D("0")
    assert row.status == DepositDeduction.Status.WITHDRAWN
    assert deposits.held(home["lease"]) == D("3000")
    returned = DepositEntry.objects.get(kind=DepositEntry.Kind.RETURNED)
    assert returned.reference == row.payment.receipt_number


def test_deposit_is_not_a_method_managers_can_record(home):
    invoice = rent(home)
    response = home["manager"].post(
        f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/",
        {"amount": "100", "method": "deposit"},
        format="json",
    )
    assert response.status_code == 400
