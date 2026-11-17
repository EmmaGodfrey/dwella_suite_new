import pytest

from apps.billing.tests import make_lease, member_client
from apps.organizations.models import Organization
from apps.tenants.details import missing_details

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup():
    org = Organization.objects.create(name="Tenant details")
    client = member_client(org, "landlord", "details-manager")
    lease = make_lease(org, active=False)
    lease.tenant.tpin = "0123456789"
    lease.tenant.national_id = "123456/10/1"
    lease.tenant.billing_address = "Plot 1, Lusaka"
    lease.tenant.save()
    return org, client, lease


def test_individual_company_and_foreign_checklists():
    individual = {
        "full_name": "Jane Banda",
        "phone_number": "+260971234567",
        "tpin": "0123456789",
        "national_id": "P123456",
        "identity_type": "passport",
        "identity_country": "MW",
        "billing_address": "Plot 1",
    }
    assert missing_details(individual) == []
    company = {**individual, "tenant_type": "company", "national_id": ""}
    assert {item["field"] for item in missing_details(company)} == {
        "company_registration",
        "representative_name",
        "representative_phone",
    }
    company.update(
        company_registration="REG-1",
        representative_name="Jane",
        representative_phone="+260971234567",
    )
    assert missing_details(company) == []


def test_tpin_is_optional_only_for_foreign_passport_holders():
    foreign = {
        "full_name": "James Whitfield",
        "phone_number": "+447700900123",
        "tpin": "",
        "national_id": "GBR123456789",
        "identity_type": "passport",
        "identity_country": "GB",
        "billing_address": "14 Cheval Place, London",
    }
    assert missing_details(foreign) == []
    changes = (
        {"identity_country": "ZM"},
        {"identity_type": "nrc"},
        {"tenant_type": "company"},
        {"identity_country": ""},
    )
    for change in changes:
        fields = {item["field"] for item in missing_details({**foreign, **change})}
        assert "tpin" in fields


def test_missing_filter_skips_foreign_passport_without_tpin(setup):
    org, client, lease = setup
    lease.tenant.tpin = ""
    lease.tenant.identity_type = "passport"
    lease.tenant.identity_country = "GB"
    lease.tenant.save()
    rows = client.get("/api/v1/tenants/?details=missing").json()["response_data"]
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert lease.tenant.public_id not in {str(row.get("public_id", row.get("id"))) for row in rows}
    lease.tenant.identity_country = "ZM"
    lease.tenant.save()
    rows = client.get("/api/v1/tenants/?details=missing").json()["response_data"]
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert any(row["full_name"] == lease.tenant.full_name for row in rows)


def test_list_masks_identifiers_detail_edits_and_missing_filter(setup):
    _, client, lease = setup
    listed = client.get("/api/v1/tenants/").json()["response_data"][0]
    assert listed["tpin"] == "••••6789"
    assert listed["national_id"] == "••••10/1"
    path = f"/api/v1/tenants/{lease.tenant.public_id}/"
    assert client.get(path).json()["response_data"]["tpin"] == "0123456789"
    assert client.patch(path, {"tpin": "wrong"}, format="json").status_code == 400
    assert client.patch(path, {"representative_phone": "123"}, format="json").status_code == 400
    assert client.patch(path, {"identity_country": "Zambia"}, format="json").status_code == 400
    response = client.patch(path, {"tpin": ""}, format="json")
    assert response.status_code == 200
    assert response.json()["response_data"]["missing_details"] == [
        {"field": "tpin", "label": "TPIN"}
    ]
    filtered = client.get("/api/v1/tenants/?details=missing").json()["response_data"]
    assert len(filtered) == 1


def test_tenant_details_remain_workspace_scoped(setup):
    _, _, lease = setup
    outside = Organization.objects.create(name="Outside details")
    client = member_client(outside, "landlord", "outside-details")
    assert client.get(f"/api/v1/tenants/{lease.tenant.public_id}/").status_code == 404
    tenant = member_client(lease.organization, "tenant", "details-tenant")
    assert tenant.get(f"/api/v1/tenants/{lease.tenant.public_id}/").status_code == 403
