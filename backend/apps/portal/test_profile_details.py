"""Tenants completing their own receipt details from the portal."""

import pytest
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.portal import tests as portal_tests
from apps.portal.tests import account, data

# Reuse the portal tenant fixture.
home = portal_tests.home

pytestmark = pytest.mark.django_db
URL = "/api/v1/portal/profile/"


def blank_details(tenant, **extra):
    for key in ("tpin", "billing_address", "national_id"):
        setattr(tenant, key, "")
    for key, value in extra.items():
        setattr(tenant, key, value)
    tenant.save()


def test_profile_lists_missing_receipt_details(home):
    blank_details(home["lease"].tenant)
    body = data(home["client"].get(URL))
    assert {item["field"] for item in body["missing_details"]} >= {
        "tpin",
        "billing_address",
        "national_id",
    }
    assert body["locked_fields"] == []


def test_tenant_completes_details_and_receipt_unblocks(home):
    tenant = home["lease"].tenant
    blank_details(tenant)
    client = home["client"]
    receipt_url = f"/api/v1/portal/payments/{home['payment'].public_id}/"
    home["payment"].created_at = tenant.document_requirements_since
    home["payment"].save(update_fields=["created_at"])
    assert data(client.get(receipt_url))["missing_details"]

    response = client.patch(
        URL,
        {
            "tpin": "1002003004",
            "billing_address": "  Plot 9, Kafue Road, Lusaka  ",
            "national_id": "123456/10/1",
            "identity_type": "nrc",
            "identity_country": "zm",
        },
        format="json",
    )
    assert response.status_code == 200, response.content
    body = data(response)
    assert body["missing_details"] == []
    assert set(body["locked_fields"]) == {"national_id", "identity_type", "identity_country"}
    tenant.refresh_from_db()
    assert tenant.billing_address == "Plot 9, Kafue Road, Lusaka"
    assert tenant.identity_country == "ZM"
    assert data(client.get(receipt_url))["missing_details"] == []

    event = AuditEvent.objects.get(action="tenant.details_updated_by_tenant")
    # The country already defaulted to ZM, so only real changes are listed.
    assert event.metadata["fields"] == ["billing_address", "national_id", "tpin"]
    # Values never go into the audit trail.
    assert "1002003004" not in str(event.metadata)
    assert not AuditEvent.objects.filter(action="tenant.contact_updated_by_tenant").exists()


def test_tenant_can_update_tpin_and_address_later(home):
    tenant = home["lease"].tenant
    blank_details(tenant, tpin="1002003004", billing_address="Old address")
    response = home["client"].patch(
        URL, {"tpin": "2002003004", "billing_address": "New address"}, format="json"
    )
    assert response.status_code == 200
    tenant.refresh_from_db()
    assert (tenant.tpin, tenant.billing_address) == ("2002003004", "New address")


def test_recorded_identity_is_locked_for_the_tenant(home):
    tenant = home["lease"].tenant
    blank_details(tenant, national_id="123456/10/1")
    client = home["client"]
    for payload in (
        {"national_id": "999999/10/1"},
        {"identity_country": "KE"},
        {"identity_type": "passport"},
    ):
        response = client.patch(URL, payload, format="json")
        assert response.status_code == 400, payload
        assert "property manager" in response.content.decode()
    tenant.refresh_from_db()
    assert tenant.national_id == "123456/10/1"
    # Sending the same recorded value back is harmless.
    assert client.patch(URL, {"national_id": "123456/10/1"}, format="json").status_code == 200


def test_tenant_cannot_change_read_only_fields(home):
    tenant = home["lease"].tenant
    name, email, kind = tenant.full_name, tenant.email, tenant.tenant_type
    response = home["client"].patch(
        URL,
        {"full_name": "Someone Else", "email": "x@example.com", "tenant_type": "company"},
        format="json",
    )
    assert response.status_code == 200
    tenant.refresh_from_db()
    assert (tenant.full_name, tenant.email, tenant.tenant_type) == (name, email, kind)


def test_invalid_details_are_rejected(home):
    tenant = home["lease"].tenant
    blank_details(tenant, tpin="1002003004", billing_address="Plot 9")
    client = home["client"]
    cases = [
        ({"tpin": "12345"}, "tpin"),
        ({"tpin": "12345abcde"}, "tpin"),
        ({"tpin": "１２３４５６７８９０"}, "tpin"),
        ({"identity_country": "Zambia"}, "identity_country"),
        ({"identity_type": "badge"}, "identity_type"),
        ({"billing_address": "x" * 1001}, "billing_address"),
        ({"tpin": ""}, "tpin"),
        ({"billing_address": "   "}, "billing_address"),
    ]
    for payload, field in cases:
        response = client.patch(URL, payload, format="json")
        assert response.status_code == 400, payload
        assert field in response.content.decode(), payload
    tenant.refresh_from_db()
    assert (tenant.tpin, tenant.billing_address) == ("1002003004", "Plot 9")


def test_profile_details_need_a_linked_tenant(home):
    payload = {"tpin": "1002003004"}
    assert APIClient().patch(URL, payload, format="json").status_code in {401, 403}
    _, manager = account(home["org"], "landlord", "details-manager")
    assert manager.patch(URL, payload, format="json").status_code == 403
    _, unlinked = account(home["org"], "tenant", "details-unlinked")
    assert unlinked.patch(URL, payload, format="json").status_code == 403
    # The neighbour's record is untouched by this tenant's edits.
    neighbour = home["neighbour"].tenant
    before = neighbour.tpin
    home["client"].patch(URL, {"tpin": "3002003004"}, format="json")
    neighbour.refresh_from_db()
    assert neighbour.tpin == before
