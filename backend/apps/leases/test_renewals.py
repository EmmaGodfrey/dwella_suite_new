from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.billing.models import Invoice
from apps.billing.services import generate_rent_invoices
from apps.billing.tests import make_lease, member_client
from apps.documents.models import DocumentVersion
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Unit
from apps.tenants.models import Tenant

from .models import Lease
from .services import start_due_renewals

pytestmark = pytest.mark.django_db
TODAY = timezone.localdate()


@pytest.fixture
def setup():
    org = Organization.objects.create(name="Renewal portfolio")
    client = member_client(org, "landlord", "renewal-owner")
    lease = make_lease(org)
    return org, client, lease


def data(response):
    return response.json()["response_data"]


def renew(client, lease, **body):
    body.setdefault("end_date", str(lease.end_date + timedelta(days=365)))
    return client.post(f"/api/v1/leases/{lease.public_id}/renew/", body, format="json")


def age(lease, renewal):
    """Move both terms so the renewal's start date is today."""
    lease.start_date, lease.end_date = TODAY - timedelta(days=365), TODAY - timedelta(days=1)
    lease.save(update_fields=["start_date", "end_date"])
    renewal.start_date, renewal.end_date = TODAY, TODAY + timedelta(days=364)
    renewal.save(update_fields=["start_date", "end_date"])


def sign(renewal, org):
    DocumentVersion.objects.create(
        organization=org, kind="lease", lease=renewal, version=1, status="signed",
        snapshot={"reference": renewal.reference}, source_fingerprint="x",
        unsigned_pdf=b"%PDF", pdf=b"%PDF", sha256="b" * 64, page_count=1,
        created_by=OrganizationMembership.objects.filter(organization=org).first().user,
    )


def test_renewal_copies_terms_into_a_draft_starting_the_next_day(setup):
    org, client, lease = setup
    response = renew(client, lease, monthly_rent="4200.00")
    assert response.status_code == 201
    body = data(response)
    renewal = Lease.objects.get(public_id=body["id"])
    assert renewal.status == "draft" and renewal.renewal_of == lease
    assert renewal.start_date == lease.end_date + timedelta(days=1)
    assert (renewal.tenant, renewal.unit) == (lease.tenant, lease.unit)
    assert renewal.monthly_rent == Decimal("4200.00")
    assert renewal.late_fee_percent == lease.late_fee_percent
    assert body["renewal_of_reference"] == lease.reference
    original = data(client.get(f"/api/v1/leases/{lease.public_id}/"))
    assert original["renewal"]["id"] == body["id"]
    # The draft is editable, except for what makes it a renewal.
    url = f"/api/v1/leases/{renewal.public_id}/"
    assert client.patch(url, {"monthly_rent": "4100.00"}, format="json").status_code == 200
    moved = client.patch(url, {"start_date": str(TODAY)}, format="json")
    assert moved.status_code == 400
    # The running lease can still be edited while its renewal is drafted.
    notes = client.patch(f"/api/v1/leases/{lease.public_id}/", {"notes": "x"}, format="json")
    assert notes.status_code == 200


def test_only_one_renewal_and_only_from_an_active_lease(setup):
    org, client, lease = setup
    assert renew(client, lease).status_code == 201
    assert renew(client, lease).status_code == 400
    draft = make_lease(org, unit_name="2B", phone="+260975550000", active=False)
    assert renew(client, draft).status_code == 400
    early = renew(client, make_lease(org, unit_name="2C", phone="+260975550001"),
                  end_date=str(TODAY))
    assert early.status_code == 400


def test_a_renewal_holds_the_unit_against_other_leases(setup):
    org, client, lease = setup
    renew(client, lease)
    other = Tenant.objects.create(
        organization=org, full_name="Someone", phone_number="+260970000001"
    )
    lease.status = "ended"
    lease.save(update_fields=["status"])
    response = client.post(
        "/api/v1/leases/",
        {"tenant": str(other.public_id), "unit": str(lease.unit.public_id),
         "start_date": str(TODAY), "end_date": str(TODAY + timedelta(days=300))},
        format="json",
    )
    assert response.status_code == 400
    assert "open lease" in response.content.decode()


def test_database_allows_one_active_lease_per_unit(setup):
    _, client, lease = setup
    renewal = Lease.objects.get(public_id=data(renew(client, lease))["id"])
    renewal.status = "active"
    with pytest.raises(IntegrityError), transaction.atomic():
        renewal.save(update_fields=["status"])


def test_starting_a_renewal_waits_for_its_date_then_hands_over(setup):
    org, client, lease = setup
    renewal = Lease.objects.get(public_id=data(renew(client, lease))["id"])
    url = f"/api/v1/leases/{renewal.public_id}/activate/"
    assert client.post(url).status_code == 400
    age(lease, renewal)
    assert client.post(url).status_code == 200
    lease.refresh_from_db()
    renewal.refresh_from_db()
    assert (lease.status, renewal.status) == ("ended", "active")
    assert Unit.objects.get(pk=lease.unit_id).occupancy_status == "occupied"
    assert Tenant.objects.get(pk=lease.tenant_id).status == "active"


def test_signed_renewals_start_automatically_and_bill_once(setup):
    org, client, lease = setup
    renewal = Lease.objects.get(public_id=data(renew(client, lease))["id"])
    age(lease, renewal)
    assert start_due_renewals() == []  # Unsigned: waits for the manager.
    alerts = data(client.get("/api/v1/notifications/"))["items"]
    assert any(item["id"].startswith(f"renewal:{renewal.public_id}") for item in alerts)
    sign(renewal, org)
    assert [item.pk for item in start_due_renewals()] == [renewal.pk]
    lease.refresh_from_db()
    assert lease.status == "ended"
    month = TODAY.replace(day=1)
    generate_rent_invoices(org, month)
    generate_rent_invoices(org, month)
    assert Invoice.objects.filter(period_start=month, lease=renewal).count() == 1


def test_a_mid_month_handover_bills_the_month_once(setup):
    org, client, lease = setup
    month = TODAY.replace(day=1)
    generate_rent_invoices(org, month)  # The old lease's rent for this month.
    renewal = Lease.objects.get(public_id=data(renew(client, lease))["id"])
    age(lease, renewal)
    sign(renewal, org)
    start_due_renewals()
    generate_rent_invoices(org, month)
    rent = Invoice.objects.filter(period_start=month, tenant=lease.tenant)
    assert list(rent.values_list("lease_id", flat=True)) == [lease.pk]
    next_month = (month + timedelta(days=32)).replace(day=1)
    generate_rent_invoices(org, next_month)
    assert Invoice.objects.get(period_start=next_month, tenant=lease.tenant).lease == renewal


def test_expiry_alert_gives_way_to_a_renewal(setup):
    org, client, lease = setup
    lease.end_date = TODAY + timedelta(days=10)
    lease.save(update_fields=["end_date"])
    expiring = f"lease:{lease.public_id}:"
    alerts = data(client.get("/api/v1/notifications/"))["items"]
    assert any(item["id"].startswith(expiring) for item in alerts)
    renew(client, lease)
    alerts = data(client.get("/api/v1/notifications/"))["items"]
    assert not any(item["id"].startswith(expiring) for item in alerts)
