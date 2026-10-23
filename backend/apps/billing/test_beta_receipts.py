from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Invoice, Payment
from apps.billing.services import generate_rent_invoices, record_payment
from apps.billing.tests import THIS_MONTH, make_lease, member_client
from apps.organizations.models import Organization

pytestmark = pytest.mark.django_db


@pytest.fixture
def portfolio():
    org = Organization.objects.create(name="Receipt test", email="rent@example.com")
    client = member_client(org, "landlord", "receipt-owner")
    make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get(organization=org)
    invoice.due_date = timezone.localdate() - timedelta(days=10)
    invoice.save(update_fields=["due_date"])
    payment = record_payment(
        invoice=invoice, amount=Decimal("1000"), method="cash", paid_on=timezone.localdate()
    )
    return org, client, invoice, payment


def test_receipt_detail_and_history(portfolio):
    org, client, invoice, payment = portfolio
    response = client.get(f"/api/v1/billing/payments/{payment.public_id}/")
    assert response.status_code == 200
    receipt = response.json()["response_data"]
    assert receipt["receipt_number"] == payment.receipt_number
    assert receipt["issuer"]["name"] == org.name
    assert receipt["issuer"]["email"] == "rent@example.com"
    assert receipt["invoice_id"] == str(invoice.public_id)
    assert receipt["current_balance"] == "2900.00"
    assert receipt["property_name"] == "Mutendere Court"
    assert not receipt["reversed_at"]
    listing = client.get("/api/v1/billing/payments/?search=RCT&reversed=false").json()
    assert listing["pagination"]["count"] == 1


def test_reversal_reopens_invoice_and_totals_and_preserves_receipt(portfolio):
    org, client, invoice, payment = portfolio
    reference = payment.receipt_number
    url = f"/api/v1/billing/payments/{payment.public_id}/reverse/"
    response = client.post(url, {"reason": "Recorded against the wrong invoice"}, format="json")
    assert response.status_code == 200
    payment.refresh_from_db()
    invoice.refresh_from_db()
    assert payment.receipt_number == reference
    assert payment.reversed_at and payment.reversed_by_id
    assert invoice.balance == Decimal("3900")
    assert invoice.status == Invoice.Status.OPEN
    summary = client.get("/api/v1/billing/invoices/summary/").json()["response_data"]
    assert summary["collected_this_month"] == "0.00"
    assert summary["outstanding"] == "3900.00"
    assert (
        client.get("/api/v1/reports/arrears/").json()["response_data"]["totals"]["balance"]
        == "3900.00"
    )
    assert client.get("/api/v1/billing/payments/?reversed=true").json()["pagination"]["count"] == 1
    assert client.post(url, {"reason": "Try reversing it again"}, format="json").status_code == 400
    assert Payment.objects.count() == 1
    # A corrected invoice may be voided once no valid payments remain.
    assert client.post(f"/api/v1/billing/invoices/{invoice.public_id}/void/").status_code == 200


@pytest.mark.parametrize(
    "payload", [{}, {"reason": " "}, {"reason": "oops"}, {"reason": "x" * 501}]
)
def test_reversal_requires_a_useful_bounded_reason(portfolio, payload):
    _, client, _, payment = portfolio
    assert (
        client.post(
            f"/api/v1/billing/payments/{payment.public_id}/reverse/", payload, format="json"
        ).status_code
        == 400
    )
    payment.refresh_from_db()
    assert payment.reversed_at is None


@pytest.mark.parametrize("role", ["tenant"])
def test_tenant_members_cannot_reverse(portfolio, role):
    org, _, _, payment = portfolio
    client = member_client(org, role, f"receipt-{role}")
    response = client.post(
        f"/api/v1/billing/payments/{payment.public_id}/reverse/",
        {"reason": "Wrong amount entered"},
        format="json",
    )
    assert response.status_code == 403


def test_receipts_are_private_and_immutable(portfolio):
    org, _, _, payment = portfolio
    url = f"/api/v1/billing/payments/{payment.public_id}/"
    assert APIClient().get(url).status_code in (401, 403)
    tenant = member_client(org, "tenant", "receipt-tenant-other")
    assert tenant.get(url).status_code == 403
    other = Organization.objects.create(name="Other receipt org")
    outsider = member_client(other, "landlord", "receipt-outsider")
    assert outsider.get(url).status_code == 404
    assert (
        outsider.post(
            url + "reverse/", {"reason": "Cross workspace attempt"}, format="json"
        ).status_code
        == 404
    )
    owner = member_client(org, "landlord", "receipt-owner-other")
    assert owner.patch(url, {"amount": "1.00"}, format="json").status_code == 405
    assert owner.delete(url).status_code == 405
    assert owner.post("/api/v1/billing/payments/", {}, format="json").status_code == 405


def test_zero_year_is_validation_error(portfolio):
    _, client, _, _ = portfolio
    assert (
        client.post(
            "/api/v1/billing/invoices/generate/", {"period": "0000-01"}, format="json"
        ).status_code
        == 400
    )


def test_backdated_payment_returns_its_own_receipt(portfolio):
    _, client, invoice, original = portfolio
    response = client.post(
        f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/",
        {
            "amount": "500.00",
            "method": "cash",
            "paid_on": str(timezone.localdate() - timedelta(days=2)),
        },
        format="json",
    )
    assert response.status_code == 201
    data = response.json()["response_data"]
    assert data["payments"][0]["id"] == str(original.public_id)
    assert data["recorded_payment"]["id"] != str(original.public_id)
    assert data["recorded_payment"]["amount"] == "500.00"


def test_payment_date_follows_zambia_before_utc_midnight(portfolio, settings, monkeypatch):
    assert settings.TIME_ZONE == "Africa/Lusaka"
    _, client, invoice, _ = portfolio
    monkeypatch.setattr(timezone, "now", lambda: datetime(2026, 10, 21, 22, 30, tzinfo=UTC))
    url = f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/"
    assert (
        client.post(
            url, {"amount": "500", "method": "cash", "paid_on": "2026-10-22"}, format="json"
        ).status_code
        == 201
    )
    assert (
        client.post(
            url, {"amount": "500", "method": "cash", "paid_on": "2026-10-23"}, format="json"
        ).status_code
        == 400
    )
