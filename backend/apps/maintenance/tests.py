import io
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.leases.services import create_lease
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import MaintenanceRequest, Vendor

User = get_user_model()
URL = "/api/v1/maintenance/requests/"
VENDORS = "/api/v1/maintenance/vendors/"


def member_client(organization, role, username):
    user = User.objects.create_user(
        username=username, password="StrongerPass123", first_name="Emmanuel", last_name="Godfrey"
    )
    OrganizationMembership.objects.create(organization=organization, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def org():
    return Organization.objects.create(name="Kafue Ridge Properties")


@pytest.fixture
def manager(org):
    return member_client(org, OrganizationMembership.Role.LANDLORD, "manager")


@pytest.fixture
def place(org):
    property_obj = Property.objects.create(
        organization=org, name="Mutendere Court", property_type="apartment", address="Plot 4471"
    )
    unit = Unit.objects.create(organization=org, property=property_obj, name="1A", rent_amount=3900)
    tenant = Tenant.objects.create(
        organization=org, full_name="Natasha Banda", phone_number="+260974123381"
    )
    today = timezone.localdate()
    create_lease(
        organization=org,
        tenant=tenant,
        unit=unit,
        start_date=today - timedelta(days=30),
        end_date=today + timedelta(days=330),
        monthly_rent=Decimal("3900"),
        activate=True,
    )
    return property_obj, unit, tenant


@pytest.fixture
def vendor(org):
    return Vendor.objects.create(organization=org, name="Mulenga Plumbing", trade="Plumbing")


def report(client, place, **extra):
    property_obj, unit, _ = place
    payload = {
        "title": "Leaking kitchen tap",
        "description": "Dripping for a week.",
        "property": str(property_obj.public_id),
        "unit": str(unit.public_id),
        "category": "plumbing",
        "priority": "high",
        **extra,
    }
    return client.post(URL, payload, format="json")


def png(name="tap.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), "navy").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@pytest.mark.django_db
def test_report_defaults_tenant_and_logs_it(manager, place):
    response = report(manager, place)
    assert response.status_code == 201
    data = response.json()["response_data"]
    assert data["reference"] == "MR-0001"
    assert data["status"] == "new"
    assert data["tenant_name"] == "Natasha Banda"  # whoever leases the unit
    assert data["reported_by_name"] == "Emmanuel Godfrey"
    detail = manager.get(f"{URL}{data['id']}/").json()["response_data"]
    assert detail["updates"][0]["body"] == "Request reported."


@pytest.mark.django_db
def test_common_area_request_has_no_unit_or_tenant(manager, place):
    response = report(manager, place, unit=None, title="Gate motor not closing")
    assert response.status_code == 201
    data = response.json()["response_data"]
    assert data["unit_name"] is None and data["tenant_name"] is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra, field",
    [
        ({"title": "  "}, "title"),
        ({"priority": "whenever"}, "priority"),
        ({"category": "magic"}, "category"),
        ({"property": "00000000-0000-0000-0000-000000000000"}, "property"),
    ],
)
def test_report_validation(manager, place, extra, field):
    response = report(manager, place, **extra)
    assert response.status_code == 400
    assert field in response.json()["response_data"]


@pytest.mark.django_db
def test_unit_must_belong_to_the_property(manager, org, place):
    other = Property.objects.create(
        organization=org, name="Roma Park Villas", property_type="house", address="Roma"
    )
    response = report(manager, place, property=str(other.public_id))
    assert response.status_code == 400
    assert "unit" in response.json()["response_data"]


@pytest.mark.django_db
def test_other_workspaces_cannot_see_or_use_records(manager, place, vendor):
    job = report(manager, place).json()["response_data"]
    outsider_org = Organization.objects.create(name="Elsewhere Lettings")
    outsider = member_client(outsider_org, OrganizationMembership.Role.LANDLORD, "outsider")
    assert outsider.get(f"{URL}{job['id']}/").status_code == 404
    assert outsider.get(URL).json()["response_data"] == []
    # Nor reference another workspace's property or vendor.
    assert report(outsider, place).status_code == 400
    own = outsider.post(
        URL,
        {"title": "x", "property": str(place[0].public_id)},
        format="json",
    )
    assert own.status_code == 400


@pytest.mark.django_db
def test_tenant_members_cannot_read_or_change(org, manager, place):
    job = report(manager, place).json()["response_data"]
    member = member_client(org, OrganizationMembership.Role.TENANT, "tenant-member")
    assert member.get(f"{URL}{job['id']}/").status_code == 403
    assert report(member, place).status_code == 403
    assert member.post(f"{URL}{job['id']}/start/").status_code == 403
    assert APIClient().get(URL).status_code in {401, 403}


@pytest.mark.django_db
def test_full_job_lifecycle_and_tenant_charge(manager, place, vendor):
    job = report(manager, place).json()["response_data"]
    when = (timezone.now() + timedelta(days=1)).isoformat()
    assigned = manager.post(
        f"{URL}{job['id']}/assign/",
        {
            "vendor": str(vendor.public_id),
            "scheduled_for": when,
            "estimated_cost": "350.00",
            "charge_to_tenant": True,
        },
        format="json",
    ).json()["response_data"]
    assert assigned["status"] == "scheduled"
    assert assigned["vendor_name"] == "Mulenga Plumbing"
    assert assigned["updates"][-1]["body"].startswith("Assigned to Mulenga Plumbing for ")

    started = manager.post(f"{URL}{job['id']}/start/").json()["response_data"]
    assert started["status"] == "in_progress" and started["started_at"]

    done = manager.post(
        f"{URL}{job['id']}/complete/", {"actual_cost": "420.00"}, format="json"
    ).json()["response_data"]
    assert done["status"] == "completed"
    assert done["invoice_reference"] == "INV-0001"
    request = MaintenanceRequest.objects.get()
    assert request.invoice.total == Decimal("420.00")
    assert request.invoice.tenant.full_name == "Natasha Banda"
    assert manager.post(f"{URL}{job['id']}/cancel/").status_code == 400  # already closed
    assert manager.post(f"{URL}{job['id']}/start/").status_code == 400


@pytest.mark.django_db
def test_charging_needs_a_tenant(manager, place, vendor):
    job = report(manager, place, unit=None).json()["response_data"]
    response = manager.post(
        f"{URL}{job['id']}/assign/",
        {"vendor": str(vendor.public_id), "charge_to_tenant": True},
        format="json",
    )
    assert response.status_code == 400
    assert "charge_to_tenant" in response.json()["response_data"]


@pytest.mark.django_db
def test_assign_rejects_negative_estimate_and_unknown_vendor(manager, place, vendor):
    job = report(manager, place).json()["response_data"]
    bad_cost = manager.post(
        f"{URL}{job['id']}/assign/",
        {"vendor": str(vendor.public_id), "estimated_cost": "-5"},
        format="json",
    )
    assert "estimated_cost" in bad_cost.json()["response_data"]
    vendor.is_active = False
    vendor.save()
    archived = manager.post(
        f"{URL}{job['id']}/assign/", {"vendor": str(vendor.public_id)}, format="json"
    )
    assert "vendor" in archived.json()["response_data"]


@pytest.mark.django_db
def test_complete_without_charge_creates_no_invoice(manager, place):
    job = report(manager, place).json()["response_data"]
    done = manager.post(f"{URL}{job['id']}/complete/", {}, format="json").json()
    assert done["response_data"]["invoice_id"] is None


@pytest.mark.django_db
def test_cancel_logs_the_reason(manager, place):
    job = report(manager, place).json()["response_data"]
    data = manager.post(
        f"{URL}{job['id']}/cancel/", {"reason": "Tenant fixed it."}, format="json"
    ).json()["response_data"]
    assert data["status"] == "cancelled"
    assert data["updates"][-1]["body"] == "Cancelled. Tenant fixed it."


@pytest.mark.django_db
def test_replies_and_internal_notes(manager, place):
    job = report(manager, place).json()["response_data"]
    url = f"{URL}{job['id']}/updates/"
    assert manager.post(url, {"body": "   "}, format="json").status_code == 400
    assert manager.post(url, {"body": "x" * 2001}, format="json").status_code == 400
    manager.post(url, {"body": "Plumber coming Tuesday."}, format="json")
    data = manager.post(
        url, {"body": "Quoted K350 last time.", "is_internal": True}, format="json"
    ).json()["response_data"]
    comments = [u for u in data["updates"] if u["kind"] == "comment"]
    assert [c["is_internal"] for c in comments] == [False, True]
    assert comments[0]["author_name"] == "Emmanuel Godfrey"


@pytest.mark.django_db
def test_photo_upload_checks_type(manager, place, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    job = report(manager, place).json()["response_data"]
    url = f"{URL}{job['id']}/photos/"
    ok = manager.post(url, {"image": png()}, format="multipart")
    assert ok.status_code == 201
    assert len(ok.json()["response_data"]["photos"]) == 1
    fake = SimpleUploadedFile("tap.png", b"not an image", content_type="image/png")
    assert manager.post(url, {"image": fake}, format="multipart").status_code == 400


@pytest.mark.django_db
def test_board_filter_and_summary(manager, place, vendor):
    open_job = report(manager, place, priority="urgent").json()["response_data"]
    old = report(manager, place, title="Old job").json()["response_data"]
    manager.post(f"{URL}{old['id']}/complete/", {}, format="json")
    MaintenanceRequest.objects.filter(public_id=old["id"]).update(
        completed_at=timezone.now() - timedelta(days=10)
    )
    recent = report(manager, place, title="Recent job").json()["response_data"]
    manager.post(f"{URL}{recent['id']}/complete/", {}, format="json")

    board = {row["id"] for row in manager.get(f"{URL}?board=true").json()["response_data"]}
    assert board == {open_job["id"], recent["id"]}

    summary = manager.get(f"{URL}summary/").json()["response_data"]
    assert summary["open"] == 1
    assert summary["urgent"] == 1
    assert summary["unassigned"] == 1
    assert summary["average_days_to_close"] is not None


@pytest.mark.django_db
def test_vendor_names_are_unique_and_used_vendors_are_archived(manager, place, vendor):
    duplicate = manager.post(VENDORS, {"name": "mulenga plumbing"}, format="json")
    assert duplicate.status_code == 400
    spare = manager.post(VENDORS, {"name": "KeySafe", "trade": "Locks"}, format="json")
    assert spare.status_code == 201

    job = report(manager, place).json()["response_data"]
    manager.post(f"{URL}{job['id']}/assign/", {"vendor": str(vendor.public_id)}, format="json")
    listed = {v["name"]: v for v in manager.get(VENDORS).json()["response_data"]}
    assert listed["Mulenga Plumbing"]["open_jobs"] == 1

    assert manager.delete(f"{VENDORS}{vendor.public_id}/").status_code == 204
    vendor.refresh_from_db()
    assert vendor.is_active is False  # kept for job history
    assert manager.delete(f"{VENDORS}{spare.json()['response_data']['id']}/").status_code == 204
    assert not Vendor.objects.filter(name="KeySafe").exists()
