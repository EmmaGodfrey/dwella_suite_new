"""Regressions for the independent review of property teams (13 November 2026)."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.billing.models import Invoice, InvoiceLine
from apps.documents.models import DocumentVersion
from apps.documents.snapshots import fingerprint, lease_source
from apps.payments.models import Collection, Destination, Payout
from apps.properties.models import Property
from apps.tenants.models import Tenant

from .models import CoverSession
from .test_property_teams import rows

pytestmark = pytest.mark.django_db
INVOICES = "/api/v1/billing/invoices/"


def charge(tenant, lease=None):
    return {
        "tenant": str(tenant.public_id),
        **({"lease": str(lease.public_id)} if lease else {}),
        "due_date": str(timezone.localdate()),
        "lines": [{"kind": "other", "description": "Review charge", "amount": "50.00"}],
    }


def next_month():
    return (timezone.localdate().replace(day=1) + timedelta(days=32)).replace(day=1)


# --- A refused write leaves nothing behind -----------------------------------------


def test_manager_charge_needs_a_lease_and_a_refusal_saves_nothing(team):
    tenant = team["lease_a"].tenant
    invoices, lines = Invoice.objects.count(), InvoiceLine.objects.count()

    refused = team["a"].post(INVOICES, charge(tenant), format="json")
    assert refused.status_code == 400, refused.content
    assert "tenant" in refused.json()["response_data"]
    assert (Invoice.objects.count(), InvoiceLine.objects.count()) == (invoices, lines)

    # With the lease the charge lands on the manager's own property.
    made = team["a"].post(INVOICES, charge(tenant, team["lease_a"]), format="json")
    assert made.status_code == 201, made.content
    # Another manager's lease is not offered at all.
    other = team["a"].post(INVOICES, charge(team["lease_b"].tenant, team["lease_b"]), format="json")
    assert other.status_code == 400
    # A property admin may still raise a charge that belongs to no lease.
    assert team["admin"].post(INVOICES, charge(tenant), format="json").status_code == 201
    assert Invoice.objects.count() == invoices + 2


def test_a_refusal_after_saving_undoes_the_write(team, monkeypatch):
    from apps.common import viewsets

    def refuse(self, instance):
        raise PermissionDenied("This property is not assigned to you.")

    monkeypatch.setattr(viewsets.OrganizationScopedModelViewSet, "check_saved", refuse)
    target = f"/api/v1/properties/{team['alpha'].public_id}/"
    response = team["a"].patch(target, {"name": "Renamed"}, format="json")
    assert response.status_code == 403
    assert Property.objects.get(pk=team["alpha"].pk).name == "Alpha Court"

    created = team["a"].post(
        "/api/v1/tenants/",
        {"full_name": "Refused Person", "phone_number": "+260970009999"},
        format="json",
    )
    assert created.status_code == 403, created.content
    assert not Tenant.objects.filter(full_name="Refused Person").exists()


# --- Receiving account and payout stay with property admins -------------------------


@pytest.fixture
def collection(team):
    destination = Destination.objects.create(
        organization=team["org"],
        phone="+260971234567",
        operator="mtn",
        account_name="Private admin receiving account",
        approved_by=team["admin"].user,
        approval_reason="Review fixture",
    )
    row = Collection.objects.create(
        organization=team["org"],
        invoice=Invoice.objects.filter(lease=team["lease_a"]).first(),
        initiated_by=team["admin"].user,
        destination=destination,
        environment="test",
        idempotency_key=uuid4(),
        amount="100.00",
        debit_account_id="review",
    )
    Payout.objects.create(collection=row, amount="95.00")
    return row


def test_manager_collections_leave_out_the_receiving_account_and_payout(team, collection):
    assert team["a"].get("/api/v1/payments/destination/").status_code == 403
    response = team["a"].get("/api/v1/payments/collections/")
    seen = rows(response)
    assert len(seen) == 1
    assert "destination" not in seen[0] and "payout" not in seen[0]
    assert seen[0]["amount"] == "100.00" and seen[0]["status"]
    assert b"Private admin receiving account" not in response.content
    assert b"1234567" not in response.content

    # The other manager does not see the collection at all.
    assert rows(team["b"].get("/api/v1/payments/collections/")) == []
    admin = rows(team["admin"].get("/api/v1/payments/collections/"))[0]
    assert admin["destination"] and admin["payout"]["amount"] == "95.00"


def test_nested_online_payment_hides_the_same_details_from_managers(team, collection):
    from apps.billing.services import record_payment

    invoice = collection.invoice
    payment = record_payment(
        invoice=invoice,
        amount=invoice.balance,
        method="mobile_money",
        paid_on=timezone.localdate(),
        recorded_by=team["admin"].user,
    )
    Collection.objects.filter(pk=collection.pk).update(payment=payment)
    target = f"{INVOICES}{invoice.public_id}/"
    manager = team["a"].get(target)
    assert manager.status_code == 200
    online = manager.json()["response_data"]["payments"][0]["online_payment"]
    assert online and "destination" not in online and "payout" not in online
    assert b"Private admin receiving account" not in manager.content
    receipt = team["a"].get(f"/api/v1/billing/payments/{payment.public_id}/")
    assert receipt.status_code == 200
    assert b"Private admin receiving account" not in receipt.content
    admin = team["admin"].get(target).json()["response_data"]["payments"][0]["online_payment"]
    assert admin["destination"] and admin["payout"]


# --- Signing ----------------------------------------------------------------------


def document_for(team, lease, signer):
    return DocumentVersion.objects.create(
        organization=team["org"],
        kind="lease",
        lease=lease,
        version=1,
        snapshot={},
        source_fingerprint=fingerprint(lease_source(lease)),
        unsigned_pdf=b"",
        pdf=b"%PDF-review",
        sha256="a" * 64,
        page_count=1,
        created_by=signer,
        landlord_signer=signer,
    )


def test_assigned_manager_is_offered_the_signing_action(team):
    document = document_for(team, team["lease_a"], team["a"].user)
    target = f"/api/v1/documents/versions/{document.public_id}/"
    assert team["a"].get(target).json()["response_data"]["can_sign"] is True
    # Someone else's document is never theirs to sign.
    assert team["admin"].get(target).json()["response_data"]["can_sign"] is False
    assert team["b"].get(target).status_code == 404
    # Losing the assignment withdraws the document and the action with it.
    team["a"].membership.property_assignments.all().delete()
    assert team["a"].get(target).status_code == 404


def emails(response):
    return sorted(row["email"] for row in rows(response))


def test_signer_choices_follow_the_lease(team):
    url = "/api/v1/documents/versions/signers/"
    assert emails(team["admin"].get(url)) == ["admin@example.com"]
    lease_a = f"{url}?lease={team['lease_a'].public_id}"
    # An admin preparing a lease may choose a manager assigned to its property.
    assert emails(team["admin"].get(lease_a)) == [
        "admin@example.com",
        "anna@example.com",
        "bola@example.com",
    ]
    # A manager is offered the admins and themselves, never teammates.
    assert emails(team["a"].get(lease_a)) == ["admin@example.com", "anna@example.com"]
    assert emails(team["b"].get(lease_a)) == ["admin@example.com", "ben@example.com"]
    for bad in ("not-a-uuid", str(uuid4())):
        assert emails(team["admin"].get(f"{url}?lease={bad}")) == ["admin@example.com"]
    # Another workspace's lease id adds nobody.
    assert emails(team["outsider"].get(lease_a)) == ["olga@example.com"]


# --- Cover audit --------------------------------------------------------------------


def test_bulk_billing_under_cover_is_on_the_record(team):
    CoverSession.objects.create(
        organization=team["org"],
        manager=team["a"].membership,
        covering_for=team["b"].membership,
        reason="Ben is on leave",
        expires_at=timezone.now() + timedelta(hours=1),
    )
    period = next_month()
    body = {"period": period.strftime("%Y-%m")}
    response = team["a"].post(f"{INVOICES}generate/", body, format="json")
    assert response.status_code == 200, response.content
    assert Invoice.objects.filter(unit__property=team["beta"], period_start=period).exists()
    event = AuditEvent.objects.get(action="cover.change", actor=team["a"].user)
    # Only the covered property is attributed to the cover, not the manager's own.
    assert event.metadata["property_ids"] == [team["beta"].pk]
    assert event.metadata["reason"] == "Ben is on leave"

    # Running it again bills nothing new, so there is nothing more to record.
    assert team["a"].post(f"{INVOICES}generate/", body, format="json").status_code == 200
    assert AuditEvent.objects.filter(action="cover.change").count() == 1


def test_bulk_billing_without_a_cover_records_no_cover_change(team):
    body = {"period": next_month().strftime("%Y-%m")}
    assert team["a"].post(f"{INVOICES}generate/", body, format="json").status_code == 200
    assert not AuditEvent.objects.filter(action="cover.change").exists()


# --- Private tables -----------------------------------------------------------------


def test_team_tables_deny_external_readers_on_postgres():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL RLS")
    tables = [
        "organizations_teaminvitation",
        "organizations_teaminvitation_properties",
        "organizations_propertyassignment",
        "organizations_coversession",
    ]
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relname, relrowsecurity FROM pg_class WHERE relname = ANY(%s)", [tables]
        )
        found = dict(cursor.fetchall())
    assert found == dict.fromkeys(tables, True)
