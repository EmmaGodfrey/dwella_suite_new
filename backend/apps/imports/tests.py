import pytest

from apps.audit.models import AuditEvent
from apps.billing.tests import member_client
from apps.organizations.models import Organization
from apps.properties.models import Property, Unit
from apps.subscriptions.models import WorkspaceAccessPolicy
from apps.tenants.models import Tenant

pytestmark = pytest.mark.django_db
UNITS = "/api/v1/properties/units"
TENANTS = "/api/v1/tenants"


@pytest.fixture
def org():
    org = Organization.objects.create(name="Import portfolio")
    Property.objects.create(
        organization=org, name="Mutendere Court", property_type="apartment", address="Plot 1"
    )
    return org


@pytest.fixture
def manager(org):
    return member_client(org, "landlord", "import-manager")


def data(response):
    return response.json()["response_data"]


def preview(client, base, text):
    return client.post(f"{base}/import-preview/", {"csv": text}, format="json")


def test_templates_list_the_columns(manager):
    response = manager.get(f"{UNITS}/import-template/")
    assert response.status_code == 200
    assert response["Content-Disposition"].startswith("attachment")
    assert response.content.decode().splitlines()[0].startswith("property,unit,rent_amount")
    tenants = manager.get(f"{TENANTS}/import-template/").content.decode()
    assert tenants.splitlines()[0].startswith("full_name,phone_number")


def test_unit_preview_classifies_rows(org, manager):
    unit_property = Property.objects.get(organization=org)
    Unit.objects.create(organization=org, property=unit_property, name="1A", rent_amount=3000)
    text = (
        "﻿Property Name,Unit,Rent,Beds,Colour\n"
        "mutendere court,2A,\"K 3,500\",2,blue\n"
        "Mutendere Court,2a,3500,2,\n"
        "Mutendere Court,1A,3000,1,\n"
        "Kabulonga Flats,1,2000,,\n"
        "Mutendere Court,3A,free,,\n"
        ",,,,\n"
    )
    body = data(preview(manager, UNITS, text))
    assert [row["status"] for row in body["rows"]] == [
        "ready", "duplicate", "duplicate", "invalid", "invalid"
    ]
    assert body["counts"] == {"ready": 1, "duplicate": 2, "invalid": 2}
    assert body["ignored_columns"] == ["colour"]
    assert "row 2" in body["rows"][1]["message"]
    assert "Kabulonga Flats" in body["rows"][3]["errors"]["property"][0]
    assert "rent_amount" in body["rows"][4]["errors"]
    assert Unit.objects.count() == 1  # Preview writes nothing.


def test_unit_import_creates_ready_rows_once(org, manager):
    text = "property,unit,rent_amount\nMutendere Court,2A,3500\nMutendere Court,2B,3600\n"
    token = data(preview(manager, UNITS, text))["preview_token"]
    response = manager.post(f"{UNITS}/import-confirm/", {"preview_token": token}, format="json")
    assert response.status_code == 201
    assert data(response)["created"] == 2
    assert set(Unit.objects.values_list("name", flat=True)) == {"2A", "2B"}
    assert Unit.objects.get(name="2A").occupancy_status == "vacant"
    again = manager.post(f"{UNITS}/import-confirm/", {"preview_token": token}, format="json")
    assert again.status_code == 400
    assert Unit.objects.count() == 2
    assert AuditEvent.objects.filter(action="portfolio.units_imported").count() == 1


def test_confirm_rechecks_rows_and_creates_nothing_when_one_changed(org, manager):
    text = "property,unit,rent_amount\nMutendere Court,2A,3500\nMutendere Court,2B,3600\n"
    token = data(preview(manager, UNITS, text))["preview_token"]
    Unit.objects.create(
        organization=org, property=Property.objects.get(organization=org), name="2B",
        rent_amount=1,
    )
    response = manager.post(f"{UNITS}/import-confirm/", {"preview_token": token}, format="json")
    assert response.status_code == 400
    assert "changed since the preview" in response.content.decode()
    assert not Unit.objects.filter(name="2A").exists()


def test_a_preview_belongs_to_its_manager_and_workspace(org, manager):
    text = "property,unit,rent_amount\nMutendere Court,2A,3500\n"
    token = data(preview(manager, UNITS, text))["preview_token"]
    colleague = member_client(org, "landlord", "import-colleague")
    response = colleague.post(f"{UNITS}/import-confirm/", {"preview_token": token}, format="json")
    assert response.status_code == 400
    other = Organization.objects.create(name="Other portfolio")
    outsider = member_client(other, "landlord", "import-outsider")
    assert outsider.post(
        f"{UNITS}/import-confirm/", {"preview_token": token}, format="json"
    ).status_code == 400
    tampered = manager.post(
        f"{UNITS}/import-confirm/", {"preview_token": token[:-2] + "xx"}, format="json"
    )
    assert tampered.status_code == 400
    assert not Unit.objects.exists()


def test_missing_columns_and_tenant_role_are_refused(org, manager):
    response = preview(manager, UNITS, "property,unit\nMutendere Court,2A\n")
    assert response.status_code == 400
    assert "rent_amount" in response.content.decode()
    tenant = member_client(org, "tenant", "import-tenant")
    assert preview(tenant, UNITS, "property,unit,rent_amount\n").status_code == 403


def test_record_limits_apply_to_the_whole_import(org, manager):
    WorkspaceAccessPolicy.objects.create(organization=org, limits={"units": 1})
    text = "property,unit,rent_amount\nMutendere Court,2A,3500\nMutendere Court,2B,3600\n"
    token = data(preview(manager, UNITS, text))["preview_token"]
    response = manager.post(f"{UNITS}/import-confirm/", {"preview_token": token}, format="json")
    assert response.status_code != 201
    assert not Unit.objects.exists()


def test_tenant_import_normalises_phones_and_skips_known_tenants(org, manager):
    Tenant.objects.create(organization=org, full_name="Known", phone_number="+260971111111")
    text = (
        "Name,Phone,Email,NRC,TPIN\n"
        "Mwila  Banda,097 123 4567,MWILA@Example.com,123456/10/1,\n"
        "Chanda Phiri,0971111111,,,\n"
        "Bwalya Mulenga,+260971234567,,,\n"
        "Natasha Zulu,12345,,,\n"
        "Kondwani Tembo,0961234567,,,12345\n"
    )
    body = data(preview(manager, TENANTS, text))
    assert [row["status"] for row in body["rows"]] == [
        "ready", "duplicate", "duplicate", "invalid", "invalid"
    ]
    assert body["rows"][0]["label"] == "Mwila Banda"
    token = body["preview_token"]
    response = manager.post(f"{TENANTS}/import-confirm/", {"preview_token": token}, format="json")
    assert response.status_code == 201
    tenant = Tenant.objects.get(full_name="Mwila Banda")
    assert (tenant.phone_number, tenant.email, tenant.status) == (
        "+260971234567", "mwila@example.com", "applicant"
    )


def test_preview_queries_do_not_grow_with_the_number_of_rows(org, manager):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def queries(count):
        rows = "".join(f"Tenant {n},097{n:07d}\n" for n in range(count))
        with CaptureQueriesContext(connection) as captured:
            response = preview(manager, TENANTS, "full_name,phone_number\n" + rows)
        assert data(response)["counts"]["ready"] == count
        return len(captured)

    assert queries(5) == queries(200)
