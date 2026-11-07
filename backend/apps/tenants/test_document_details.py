from datetime import timedelta

import pytest
from django.utils import timezone

from apps.billing.models import Invoice, Payment
from apps.billing.services import generate_rent_invoices, record_payment
from apps.documents.models import DocumentVersion
from apps.leases.models import Lease
from apps.tenants.details import receipt_missing_details

from .test_details import setup  # noqa: F401

__all__ = ["setup"]

pytestmark = pytest.mark.django_db


def test_incomplete_activation_and_new_documents_blocked_payment_survives(setup):
    org, client, lease = setup
    lease.tenant.tpin = ""
    lease.tenant.save()
    assert client.post(f"/api/v1/leases/{lease.public_id}/activate/").status_code == 400
    lease.refresh_from_db()
    assert lease.status == Lease.Status.DRAFT
    # An existing obligation is still payable, even while its identity details need updating.
    Lease.objects.filter(pk=lease.pk).update(status="active")
    generate_rent_invoices(org, timezone.localdate().replace(day=1))
    invoice = Invoice.objects.get(lease=lease)
    response = client.post(f"/api/v1/billing/invoices/{invoice.public_id}/document/")
    assert response.status_code == 400
    assert not DocumentVersion.objects.exists()
    payment = record_payment(
        invoice=invoice, amount=100, method="cash", paid_on=timezone.localdate()
    )
    assert Payment.objects.filter(pk=payment.pk).exists()
    assert receipt_missing_details(payment) == [{"field": "tpin", "label": "TPIN"}]
    # Migration cutover exempts receipts that were already issued, without changing money.
    payment.tenant.document_requirements_since = payment.created_at + timedelta(seconds=1)
    assert receipt_missing_details(payment) == []


def test_saved_invoice_remains_available_after_details_become_incomplete(setup):
    org, client, lease = setup
    assert client.post(f"/api/v1/leases/{lease.public_id}/activate/").status_code == 200
    generate_rent_invoices(org, timezone.localdate().replace(day=1))
    invoice = Invoice.objects.get(lease=lease)
    response = client.post(f"/api/v1/billing/invoices/{invoice.public_id}/document/")
    assert response.status_code == 200, response.content
    document_id = response.json()["response_data"]["id"]
    lease.tenant.tpin = ""
    lease.tenant.save()
    assert client.get(f"/api/v1/documents/versions/{document_id}/pdf/").status_code == 200

