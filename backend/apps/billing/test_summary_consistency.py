"""The billing summary and the dashboard must report one figure for a month."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.billing.models import Invoice
from apps.billing.services import create_invoice, generate_rent_invoices, record_payment
from apps.billing.tests import THIS_MONTH, make_lease
from apps.billing.tests import manager as manager  # noqa: F401  (fixture)
from apps.billing.tests import org as org  # noqa: F401  (fixture)

pytestmark = pytest.mark.django_db
SUMMARY = "/api/v1/billing/invoices/summary/"


def summary(client):
    return client.get(SUMMARY).json()["response_data"]


def test_rent_issued_last_month_counts_as_billed_for_this_month(manager, org):  # noqa: F811
    lease = make_lease(org, rent="1000.00")
    generate_rent_invoices(org, THIS_MONTH)
    rent = Invoice.objects.get(lease=lease)
    # Rent for this month raised in advance, before the month began.
    rent.issue_date = THIS_MONTH - timedelta(days=3)
    rent.save(update_fields=["issue_date"])
    # Paid last month too, so no cash lands this month for it.
    record_payment(
        invoice=rent,
        amount=Decimal("1000"),
        method="cash",
        paid_on=THIS_MONTH - timedelta(days=1),
    )

    body = summary(manager)
    breakdown = body["month_breakdown"]
    assert body["billed_this_month"] == breakdown["billed"] == "1000.00"
    assert body["invoices_this_month"] == 1
    assert breakdown["paid"] == "1000.00"
    # Cash received this month is a separate, clearly named figure.
    assert body["collected_this_month"] == "0.00"


def test_billed_matches_breakdown_with_old_and_new_charges(manager, org):  # noqa: F811
    lease = make_lease(org, rent="1000.00")
    generate_rent_invoices(org, THIS_MONTH)
    # An older unpaid charge settled this month: cash in, but not billed now.
    old = create_invoice(
        organization=org,
        tenant=lease.tenant,
        lease=lease,
        issue_date=THIS_MONTH - timedelta(days=40),
        due_date=THIS_MONTH - timedelta(days=30),
        lines=[{"kind": "utility", "description": "Water", "amount": Decimal("200")}],
    )
    record_payment(invoice=old, amount=Decimal("200"), method="cash", paid_on=timezone.localdate())

    body = summary(manager)
    assert body["billed_this_month"] == body["month_breakdown"]["billed"] == "1000.00"
    assert body["invoices_this_month"] == 1
    assert body["collected_this_month"] == "200.00"
