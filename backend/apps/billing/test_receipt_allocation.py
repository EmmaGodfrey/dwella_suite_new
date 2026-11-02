"""Receipts show how each payment was split between rent and the deposit."""

# ruff: noqa: F811
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.portal.tests import data

from .deposits import allocation
from .services import create_invoice, record_payment, reverse_payment
from .test_deposits import home  # noqa: F401  (shared fixture)

pytestmark = pytest.mark.django_db
TODAY = timezone.localdate()
D = Decimal


def move_in_invoice(home):
    lease = home["lease"]
    return create_invoice(
        organization=home["org"],
        tenant=lease.tenant,
        lease=lease,
        issue_date=TODAY,
        due_date=TODAY,
        lines=[
            {"kind": "rent", "description": "Rent", "amount": D("3900")},
            {"kind": "utility", "description": "Refuse collection", "amount": D("50")},
            {"kind": "deposit", "description": "Security deposit", "amount": D("3000")},
        ],
    )


def pay(invoice, amount):
    return record_payment(invoice=invoice, amount=D(amount), method="cash", paid_on=TODAY)


def split(payment):
    return [(row["kind"], row["amount"]) for row in allocation(payment)]


def test_charges_settle_before_the_deposit(home):
    invoice = move_in_invoice(home)
    first = pay(invoice, "3000")
    second = pay(invoice, "1450")  # finishes rent and charges, starts the deposit
    third = pay(invoice, "2500")
    assert split(first) == [("charges", "3000.00")]
    assert split(second) == [("charges", "950.00"), ("deposit", "500.00")]
    assert split(third) == [("deposit", "2500.00")]
    rows = allocation(second)
    assert rows[0]["label"] == "Rent, Refuse collection"
    assert rows[1]["note"] == "Held for the tenant, refundable"
    assert {row["document"] for row in rows} == {invoice.reference}


def test_reversed_earlier_payment_moves_later_money_back_to_rent(home):
    invoice = move_in_invoice(home)
    first = pay(invoice, "3950")
    second = pay(invoice, "1000")
    assert split(second) == [("deposit", "1000.00")]
    reverse_payment(first, reason="Cheque bounced", user=home["manager_user"])
    # With the first payment gone, the second one paid rent; matches the deposit ledger.
    assert split(second) == [("charges", "1000.00")]


def test_receipts_show_the_split_to_manager_and_tenant(home):
    invoice = move_in_invoice(home)
    pay(invoice, "3950")
    payment = pay(invoice, "3000")
    manager = data(home["manager"].get(f"/api/v1/billing/payments/{payment.public_id}/"))
    assert [row["kind"] for row in manager["allocation"]] == ["deposit"]
    assert manager["deposit_held"] == "3000.00"
    tenant = data(home["tenant"].get(f"/api/v1/portal/payments/{payment.public_id}/"))
    assert tenant["allocation"] == manager["allocation"]
    assert tenant["deposit_held"] == "3000.00"


def test_rent_only_receipt_has_one_line_and_no_deposit(home):
    lease = home["lease"]
    invoice = create_invoice(
        organization=home["org"],
        tenant=lease.tenant,
        lease=lease,
        issue_date=TODAY,
        due_date=TODAY,
        lines=[{"kind": "rent", "description": "Rent", "amount": D("3900")}],
    )
    payment = pay(invoice, "1000")
    body = data(home["manager"].get(f"/api/v1/billing/payments/{payment.public_id}/"))
    assert [(r["kind"], r["amount"]) for r in body["allocation"]] == [("charges", "1000.00")]
    assert body["deposit_held"] is None
