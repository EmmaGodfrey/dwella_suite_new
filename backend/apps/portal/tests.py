from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.billing.models import Invoice
from apps.billing.services import generate_rent_invoices, record_payment
from apps.billing.tests import THIS_MONTH, make_lease
from apps.documents.models import DocumentVersion
from apps.maintenance.models import MaintenanceRequest, MaintenanceUpdate
from apps.maintenance.services import create_request
from apps.organizations.models import Organization, OrganizationMembership

pytestmark = pytest.mark.django_db
User = get_user_model()


def account(org, role, username):
    user = User.objects.create_user(username=username, email=f"{username}@example.com")
    OrganizationMembership.objects.create(organization=org, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return user, client


def data(response):
    return response.json()["response_data"]


@pytest.fixture
def home():
    org = Organization.objects.create(name="Kafue Ridge Properties", email="rent@example.com")
    lease = make_lease(org)
    neighbour = make_lease(org, unit_name="2B", phone="+260975550000")
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get(tenant=lease.tenant)
    invoice.due_date = timezone.localdate() - timedelta(days=3)
    invoice.save(update_fields=["due_date"])
    payment = record_payment(
        invoice=invoice,
        amount=Decimal("900"),
        method="cash",
        paid_on=timezone.localdate(),
        notes="Manager-only note",
    )
    user, client = account(org, "tenant", "portal-tenant")
    lease.tenant.user = user
    lease.tenant.email = user.email
    lease.tenant.save(update_fields=["user", "email"])
    return {
        "org": org, "lease": lease, "neighbour": neighbour, "invoice": invoice,
        "payment": payment, "user": user, "client": client,
    }


def test_portal_is_only_for_linked_tenants(home):
    org = home["org"]
    assert APIClient().get("/api/v1/portal/overview/").status_code in {401, 403}
    _, landlord = account(org, "landlord", "portal-manager")
    assert landlord.get("/api/v1/portal/overview/").status_code == 403
    _, unlinked = account(org, "tenant", "portal-unlinked")
    response = unlinked.get("/api/v1/portal/overview/")
    assert response.status_code == 403
    assert "not linked" in response.content.decode()
    staff = User.objects.create_user(username="portal-staff", is_staff=True)
    client = APIClient()
    client.force_authenticate(user=staff)
    assert client.get("/api/v1/portal/overview/").status_code == 403
    # Tenants still cannot reach the manager APIs.
    assert home["client"].get("/api/v1/billing/invoices/").status_code == 403


def test_archived_tenant_record_or_suspended_workspace_closes_the_portal(home):
    tenant = home["lease"].tenant
    tenant.is_active = False
    tenant.save(update_fields=["is_active"])
    assert home["client"].get("/api/v1/portal/overview/").status_code == 403
    tenant.is_active = True
    tenant.save(update_fields=["is_active"])
    home["org"].is_active = False
    home["org"].save(update_fields=["is_active"])
    assert home["client"].get("/api/v1/portal/overview/").status_code == 403


def test_overview_shows_only_the_tenants_own_figures(home):
    overview = data(home["client"].get("/api/v1/portal/overview/"))
    assert overview["balance"] == "3000.00"
    assert overview["overdue_balance"] == "3000.00"
    assert overview["next_due"]["id"] == str(home["invoice"].public_id)
    assert [lease["id"] for lease in overview["current_leases"]] == [str(home["lease"].public_id)]
    assert overview["recent_payments"][0]["receipt_number"] == home["payment"].receipt_number
    assert overview["manager"]["email"] == "rent@example.com"
    assert overview["open_repairs"] == 0


def test_invoices_payments_and_leases_are_scoped_to_the_tenant(home):
    client = home["client"]
    invoices = data(client.get("/api/v1/portal/invoices/"))
    assert [item["id"] for item in invoices] == [str(home["invoice"].public_id)]
    other = Invoice.objects.get(tenant=home["neighbour"].tenant)
    assert client.get(f"/api/v1/portal/invoices/{other.public_id}/").status_code == 404
    assert client.get(f"/api/v1/portal/leases/{home['neighbour'].public_id}/").status_code == 404
    detail = data(client.get(f"/api/v1/portal/invoices/{home['invoice'].public_id}/"))
    assert detail["balance"] == "3000.00"
    assert [p["receipt_number"] for p in detail["payments"]] == [home["payment"].receipt_number]
    receipt = data(client.get(f"/api/v1/portal/payments/{home['payment'].public_id}/"))
    assert receipt["current_balance"] == "3000.00"
    assert "notes" not in receipt and "recorded_by_name" not in receipt
    assert "Manager-only note" not in str(receipt)
    leases = data(client.get("/api/v1/portal/leases/"))
    assert [lease["id"] for lease in leases] == [str(home["lease"].public_id)]
    assert "notes" not in leases[0]


def test_draft_leases_and_unshared_documents_stay_hidden(home):
    lease = home["lease"]
    lease.status = "draft"
    lease.save(update_fields=["status"])
    client = home["client"]
    assert data(client.get("/api/v1/portal/leases/")) == []
    lease.status = "active"
    lease.save(update_fields=["status"])
    common = {
        "organization": home["org"], "kind": "lease", "lease": lease,
        "snapshot": {"reference": "L1"},
        "source_fingerprint": "x", "unsigned_pdf": b"%PDF", "pdf": b"%PDF-1.4 test",
        "sha256": "a" * 64, "page_count": 1, "created_by": home["user"],
    }
    ready = DocumentVersion.objects.create(version=1, status="ready", **common)
    signing = DocumentVersion.objects.create(version=2, status="signing", **common)
    listing = data(client.get(f"/api/v1/portal/leases/{lease.public_id}/documents/"))
    assert [doc["id"] for doc in listing["versions"]] == [str(signing.public_id)]
    assert listing["versions"][0]["awaiting_your_signature"] is True
    assert client.get(f"/api/v1/portal/documents/{ready.public_id}/pdf/").status_code == 404
    response = client.get(f"/api/v1/portal/documents/{signing.public_id}/pdf/")
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert data(client.get("/api/v1/portal/overview/"))["awaiting_signature"][0]["id"] == str(
        signing.public_id
    )


def test_tenant_can_download_their_invoice_pdf(home):
    client = home["client"]
    url = f"/api/v1/portal/invoices/{home['invoice'].public_id}"
    info = data(client.get(f"{url}/info/"))
    assert info["page_count"] >= 1
    response = client.get(f"{url}/pdf/")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    # The saved version is reused rather than rendered again.
    client.get(f"{url}/pdf/")
    assert DocumentVersion.objects.filter(invoice=home["invoice"]).count() == 1
    other = Invoice.objects.get(tenant=home["neighbour"].tenant)
    assert client.get(f"/api/v1/portal/invoices/{other.public_id}/pdf/").status_code == 404


def test_tenant_reports_and_follows_a_repair(home):
    client, lease = home["client"], home["lease"]
    response = client.post(
        "/api/v1/portal/maintenance/",
        {"title": " Kitchen tap leaking ", "category": "plumbing", "permission_to_enter": True},
        format="json",
    )
    assert response.status_code == 201
    job = MaintenanceRequest.objects.get(public_id=data(response)["id"])
    assert (job.tenant, job.unit, job.source) == (lease.tenant, lease.unit, "tenant")
    assert job.title == "Kitchen tap leaking" and job.reported_by == home["user"]
    assert AuditEvent.objects.filter(action="maintenance.tenant_reported").exists()
    MaintenanceUpdate.objects.create(request=job, body="Vendor quote 400", is_internal=True)
    url = f"/api/v1/portal/maintenance/{job.public_id}"
    reply = client.post(f"{url}/updates/", {"body": "Water is now on the floor"}, format="json")
    assert reply.status_code == 201
    bodies = [update["body"] for update in data(reply)["updates"]]
    assert "Water is now on the floor" in bodies and "Vendor quote 400" not in bodies
    assert data(client.get(f"{url}/"))["updates"][-1]["from_you"] is True
    job.status = MaintenanceRequest.Status.COMPLETED
    job.save(update_fields=["status"])
    assert client.post(f"{url}/updates/", {"body": "Thanks"}, format="json").status_code == 400
    shared = create_request(
        organization=home["org"], property=lease.unit.property, title="Gate", tenant=None
    )
    assert client.get(f"/api/v1/portal/maintenance/{shared.public_id}/").status_code == 404
    listing = data(client.get("/api/v1/portal/maintenance/"))
    assert [item["id"] for item in listing] == [str(job.public_id)]
    assert "estimated_cost" not in listing[0]


def test_repairs_need_a_current_tenancy(home):
    lease = home["lease"]
    lease.status = "ended"
    lease.save(update_fields=["status"])
    response = home["client"].post(
        "/api/v1/portal/maintenance/", {"title": "Broken window"}, format="json"
    )
    assert response.status_code == 400


def test_tenant_updates_their_phone_but_not_their_email(home):
    client = home["client"]
    response = client.patch(
        "/api/v1/portal/profile/", {"phone_number": "0977 000 111", "email": "x@example.com"},
        format="json",
    )
    assert response.status_code == 200
    tenant = home["lease"].tenant
    tenant.refresh_from_db()
    assert tenant.phone_number == "+260977000111"
    assert tenant.email == home["user"].email
    taken = client.patch(
        "/api/v1/portal/profile/", {"phone_number": "+260975550000"}, format="json"
    )
    assert taken.status_code == 400
    assert AuditEvent.objects.filter(action="tenant.contact_updated_by_tenant").count() == 1


def test_manager_removes_portal_access_and_keeps_the_records(home):
    org, tenant = home["org"], home["lease"].tenant
    _, manager = account(org, "landlord", "portal-owner")
    response = manager.post(f"/api/v1/tenants/{tenant.public_id}/remove-portal-access/")
    assert response.status_code == 200 and data(response)["removed"] is True
    tenant.refresh_from_db()
    assert tenant.user is None
    assert not OrganizationMembership.objects.filter(user=home["user"]).exists()
    assert home["client"].get("/api/v1/portal/overview/").status_code == 403
    assert Invoice.objects.filter(tenant=tenant).exists()
    assert AuditEvent.objects.filter(action="tenant.portal_access_removed").exists()
    # Tenants cannot remove access themselves.
    assert home["client"].post(
        f"/api/v1/tenants/{tenant.public_id}/remove-portal-access/"
    ).status_code == 403


def test_tenant_adds_a_photo_to_their_repair(home):
    import io

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    raw = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(raw, format="PNG")
    lease = home["lease"]
    job = create_request(
        organization=home["org"], property=lease.unit.property, unit=lease.unit,
        tenant=lease.tenant, title="Damp wall",
    )
    response = home["client"].post(
        f"/api/v1/portal/maintenance/{job.public_id}/photos/",
        {"image": SimpleUploadedFile("wall.png", raw.getvalue(), content_type="image/png")},
        format="multipart",
    )
    assert response.status_code == 201
    assert len(data(response)["photos"]) == 1
    assert job.photos.get().uploaded_by == home["user"]


def test_overview_query_count_is_bounded(home, django_assert_max_num_queries):
    with django_assert_max_num_queries(12):
        assert home["client"].get("/api/v1/portal/overview/").status_code == 200
