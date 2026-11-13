"""Property admins, assigned property managers and covering for a teammate."""

import re
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.billing.models import Invoice
from apps.billing.services import generate_rent_invoices
from apps.leases.services import create_lease
from apps.maintenance.models import MaintenanceRequest
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import (
    CoverSession,
    Organization,
    OrganizationMembership,
    PropertyAssignment,
    TeamInvitation,
)

pytestmark = pytest.mark.django_db
User = get_user_model()
Role = OrganizationMembership.Role
MONTH = timezone.localdate().replace(day=1)
TEAM = "/api/v1/organizations/team/"


def person(organization, role, name, *properties):
    user = User.objects.create_user(
        username=f"{name}@example.com",
        email=f"{name}@example.com",
        password="StrongerPass123",
        first_name=name.title(),
    )
    membership = OrganizationMembership.objects.create(
        organization=organization, user=user, role=role
    )
    for item in properties:
        PropertyAssignment.objects.create(
            organization=organization, membership=membership, property=item
        )
    client = APIClient()
    client.force_authenticate(user=user)
    client.user, client.membership = user, membership
    return client


def tenancy(organization, property_obj, unit_name, tenant_name, phone, tenant=None):
    unit = Unit.objects.create(
        organization=organization, property=property_obj, name=unit_name, rent_amount="1000.00"
    )
    tenant = tenant or Tenant.objects.create(
        organization=organization,
        full_name=tenant_name,
        phone_number=phone,
        email=f"{unit_name.lower()}@tenants.example.com",
        national_id="123456/10/1",
        tpin="0123456789",
        billing_address="Plot 1, Lusaka",
    )
    return create_lease(
        organization=organization,
        tenant=tenant,
        unit=unit,
        start_date=MONTH - timedelta(days=60),
        end_date=MONTH + timedelta(days=300),
        monthly_rent=Decimal("1000.00"),
        activate=True,
    )


@pytest.fixture
def team():
    cache.clear()
    org = Organization.objects.create(name="Kabulonga Estates")
    other = Organization.objects.create(name="Rival Lettings")
    alpha = Property.objects.create(
        organization=org, name="Alpha Court", property_type="apartment", address="1 Alpha Rd"
    )
    beta = Property.objects.create(
        organization=org, name="Beta Court", property_type="apartment", address="2 Beta Rd"
    )
    foreign = Property.objects.create(
        organization=other, name="Foreign Court", property_type="apartment", address="9 Far Rd"
    )
    lease_a = tenancy(org, alpha, "A1", "Alice Alpha", "+260970000001")
    lease_b = tenancy(org, beta, "B1", "Bob Beta", "+260970000002")
    # One person renting in both properties.
    shared_a = tenancy(org, alpha, "A2", "Sam Shared", "+260970000003")
    shared_b = tenancy(org, beta, "B2", "", "", tenant=shared_a.tenant)
    tenancy(other, foreign, "F1", "Fiona Foreign", "+260970000009")
    generate_rent_invoices(org, MONTH)
    return {
        "org": org,
        "other": other,
        "alpha": alpha,
        "beta": beta,
        "foreign": foreign,
        "lease_a": lease_a,
        "lease_b": lease_b,
        "shared_a": shared_a,
        "shared_b": shared_b,
        "admin": person(org, Role.LANDLORD, "admin"),
        "a": person(org, Role.MANAGER, "anna", alpha),
        "b": person(org, Role.MANAGER, "ben", beta),
        "both": person(org, Role.MANAGER, "bola", alpha, beta),
        "none": person(org, Role.MANAGER, "nia"),
        "outsider": person(other, Role.LANDLORD, "olga"),
    }


def rows(response):
    assert response.status_code == 200, response.content
    return response.json()["response_data"]


def names(response, key="name"):
    return sorted(row[key] for row in rows(response))


# --- Who sees what ---------------------------------------------------------------


def test_admin_sees_every_property_and_managers_see_only_assigned(team):
    assert names(team["admin"].get("/api/v1/properties/")) == ["Alpha Court", "Beta Court"]
    assert names(team["a"].get("/api/v1/properties/")) == ["Alpha Court"]
    assert names(team["b"].get("/api/v1/properties/")) == ["Beta Court"]
    assert names(team["both"].get("/api/v1/properties/")) == ["Alpha Court", "Beta Court"]
    assert names(team["none"].get("/api/v1/properties/")) == []

    assert names(team["a"].get("/api/v1/properties/units/")) == ["A1", "A2"]
    assert {row["property_name"] for row in rows(team["a"].get("/api/v1/leases/"))} == {
        "Alpha Court"
    }
    assert {row["property_name"] for row in rows(team["a"].get("/api/v1/billing/invoices/"))} == {
        "Alpha Court"
    }
    assert len(rows(team["admin"].get("/api/v1/billing/invoices/"))) == 4
    assert rows(team["none"].get("/api/v1/billing/invoices/")) == []
    assert names(team["a"].get("/api/v1/tenants/"), "full_name") == ["Alice Alpha", "Sam Shared"]
    assert names(team["none"].get("/api/v1/tenants/"), "full_name") == []


def test_access_payload_tells_admin_and_manager_apart(team):
    admin = team["admin"].get("/api/v1/accounts/me/").json()["response_data"]["access"]
    manager = team["a"].get("/api/v1/accounts/me/").json()["response_data"]["access"]
    assert admin["persona"] == manager["persona"] == "landlord"
    assert (admin["role"], admin["is_property_admin"], admin["property_scope"]) == (
        "landlord", True, "all",
    )
    assert (manager["role"], manager["is_property_admin"], manager["property_scope"]) == (
        "manager", False, "assigned",
    )
    assert manager["can_view_portfolio"] and manager["can_manage_properties"]
    assert not manager["can_manage_organization"]


def test_manager_cannot_open_or_change_another_managers_records(team):
    a, lease_b = team["a"], team["lease_b"]
    invoice_b = Invoice.objects.get(lease=lease_b)
    for path in (
        f"/api/v1/properties/{team['beta'].public_id}/",
        f"/api/v1/properties/units/{lease_b.unit.public_id}/",
        f"/api/v1/leases/{lease_b.public_id}/",
        f"/api/v1/tenants/{lease_b.tenant.public_id}/",
        f"/api/v1/billing/invoices/{invoice_b.public_id}/",
        f"/api/v1/billing/deposits/{lease_b.public_id}/",
        f"/api/v1/properties/{team['foreign'].public_id}/",
    ):
        assert a.get(path).status_code == 404, path
    assert (
        a.patch(
            f"/api/v1/properties/units/{lease_b.unit.public_id}/", {"name": "Mine"}, format="json"
        ).status_code
        == 404
    )
    paid = a.post(
        f"/api/v1/billing/invoices/{invoice_b.public_id}/record-payment/",
        {"amount": "10.00", "method": "cash"},
        format="json",
    )
    assert paid.status_code == 404
    assert a.post(f"/api/v1/leases/{lease_b.public_id}/end/").status_code == 404
    invoice_b.refresh_from_db()
    assert invoice_b.amount_paid == 0


def test_manager_cannot_attach_new_records_to_unassigned_properties(team):
    a = team["a"]
    unit = a.post(
        "/api/v1/properties/units/",
        {"property": str(team["beta"].public_id), "name": "Sneaky", "rent_amount": "10.00"},
        format="json",
    )
    assert unit.status_code == 400 and "property" in unit.json()["response_data"]
    assert not Unit.objects.filter(name="Sneaky").exists()

    spare = Unit.objects.create(
        organization=team["org"], property=team["beta"], name="B9", rent_amount="500.00"
    )
    lease = a.post(
        "/api/v1/leases/",
        {
            "tenant": str(team["lease_a"].tenant.public_id),
            "unit": str(spare.public_id),
            "start_date": str(MONTH),
            "end_date": str(MONTH + timedelta(days=365)),
        },
        format="json",
    )
    assert lease.status_code == 400 and "unit" in lease.json()["response_data"]

    repair = a.post(
        "/api/v1/maintenance/requests/",
        {"property": str(team["beta"].public_id), "title": "Gate", "category": "other"},
        format="json",
    )
    assert repair.status_code == 400 and "property" in repair.json()["response_data"]
    assert MaintenanceRequest.objects.count() == 0

    # A unit cannot be moved out of the manager's properties either.
    own_unit = team["lease_a"].unit
    moved = a.patch(
        f"/api/v1/properties/units/{own_unit.public_id}/",
        {"property": str(team["beta"].public_id)},
        format="json",
    )
    assert moved.status_code == 400
    own_unit.refresh_from_db()
    assert own_unit.property_id == team["alpha"].pk


def test_manager_works_normally_inside_assigned_property(team):
    a = team["a"]
    created = a.post(
        "/api/v1/properties/units/",
        {"property": str(team["alpha"].public_id), "name": "A3", "rent_amount": "900.00"},
        format="json",
    )
    assert created.status_code == 201, created.content
    renamed = a.patch(
        f"/api/v1/properties/{team['alpha'].public_id}/", {"town": "Lusaka"}, format="json"
    )
    assert renamed.status_code == 200
    invoice = Invoice.objects.get(lease=team["lease_a"])
    paid = a.post(
        f"/api/v1/billing/invoices/{invoice.public_id}/record-payment/",
        {"amount": "100.00", "method": "cash"},
        format="json",
    )
    assert paid.status_code == 201, paid.content
    repair = a.post(
        "/api/v1/maintenance/requests/",
        {"property": str(team["alpha"].public_id), "title": "Leaking tap", "category": "plumbing"},
        format="json",
    )
    assert repair.status_code == 201, repair.content
    assert names(team["b"].get("/api/v1/maintenance/requests/"), "title") == []
    assert names(a.get("/api/v1/maintenance/requests/"), "title") == ["Leaking tap"]


def test_only_admins_add_or_delete_properties_and_run_imports(team):
    payload = {"name": "Gamma Court", "property_type": "house", "address": "3 Gamma Rd"}
    assert team["a"].post("/api/v1/properties/", payload, format="json").status_code == 403
    assert team["a"].delete(f"/api/v1/properties/{team['alpha'].public_id}/").status_code == 403
    assert team["admin"].post("/api/v1/properties/", payload, format="json").status_code == 201
    assert team["a"].get("/api/v1/tenants/import-template/").status_code == 403
    assert team["a"].post("/api/v1/properties/units/import-preview/", {}).status_code == 403
    assert team["admin"].get("/api/v1/tenants/import-template/").status_code == 200


def test_tenant_renting_in_two_properties_shows_each_manager_only_their_side(team):
    shared = team["shared_a"].tenant
    for key, property_name in (("a", "Alpha Court"), ("b", "Beta Court")):
        detail = team[key].get(f"/api/v1/tenants/{shared.public_id}/").json()["response_data"]
        assert detail["current_lease"]["property_name"] == property_name
        # One month's rent in their own property, not the tenant's whole debt.
        assert detail["balance"] == "1000.00"
        statement = team[key].get(
            "/api/v1/reports/tenant-statement/", {"tenant": str(shared.public_id)}
        )
        assert statement.status_code == 200, statement.content
        assert property_name in statement.content.decode()
        assert ("Beta Court" if key == "a" else "Alpha Court") not in statement.content.decode()
    admin = team["admin"].get(f"/api/v1/tenants/{shared.public_id}/").json()["response_data"]
    assert admin["balance"] == "2000.00"

    leases = rows(team["a"].get("/api/v1/leases/", {"tenant": str(shared.public_id)}))
    assert [row["property_name"] for row in leases] == ["Alpha Court"]
    # Filtering by the other property reveals nothing about the tenant's other lease.
    assert rows(team["a"].get("/api/v1/tenants/", {"property": str(team["beta"].public_id)})) == []
    # Archiving or removing portal access would change the tenant for both properties.
    assert team["a"].post(f"/api/v1/tenants/{shared.public_id}/archive/").status_code == 403
    assert (
        team["a"].post(f"/api/v1/tenants/{shared.public_id}/remove-portal-access/").status_code
        == 403
    )
    assert team["a"].patch(
        f"/api/v1/tenants/{shared.public_id}/", {"notes": "Prefers WhatsApp"}, format="json"
    ).status_code == 200


def test_tenant_without_a_lease_stays_with_the_manager_who_added_them(team):
    created = team["a"].post(
        "/api/v1/tenants/",
        {"full_name": "Paula Prospect", "phone_number": "0971234567"},
        format="json",
    )
    assert created.status_code == 201, created.content
    tenant_id = created.json()["response_data"]["id"]
    assert team["a"].get(f"/api/v1/tenants/{tenant_id}/").status_code == 200
    assert team["b"].get(f"/api/v1/tenants/{tenant_id}/").status_code == 404
    assert team["admin"].get(f"/api/v1/tenants/{tenant_id}/").status_code == 200
    assert "Paula Prospect" not in names(team["b"].get("/api/v1/tenants/"), "full_name")


def test_totals_reports_and_exports_count_only_assigned_properties(team):
    a, admin = team["a"], team["admin"]
    dashboard = a.get("/api/v1/properties/dashboard/").json()["response_data"]
    assert dashboard["properties"]["total"] == 1 and dashboard["units"]["total"] == 2
    assert admin.get("/api/v1/properties/dashboard/").json()["response_data"]["units"]["total"] == 4

    summary = a.get("/api/v1/billing/invoices/summary/").json()["response_data"]
    assert summary["billed_this_month"] == "2000.00"
    assert (
        admin.get("/api/v1/billing/invoices/summary/").json()["response_data"]["billed_this_month"]
        == "4000.00"
    )

    rent_roll = a.get("/api/v1/reports/rent-roll/").json()["response_data"]
    assert rent_roll["totals"]["units"] == 2
    assert {row["property"] for row in rent_roll["rows"]} == {"Alpha Court"}
    export = a.get("/api/v1/reports/rent-roll/?export=csv")
    body = b"".join(export.streaming_content if export.streaming else [export.content]).decode()
    assert "Alpha Court" in body and "Beta Court" not in body

    foreign = a.get("/api/v1/reports/rent-roll/", {"property": str(team["beta"].public_id)})
    assert foreign.status_code == 400
    other_tenant = a.get(
        "/api/v1/reports/tenant-statement/", {"tenant": str(team["lease_b"].tenant.public_id)}
    )
    assert other_tenant.status_code == 400
    empty = team["none"].get("/api/v1/reports/arrears/").json()["response_data"]
    assert empty["rows"] == [] and empty["totals"]["invoices"] == 0


def test_generate_invoices_bills_only_the_managers_properties(team):
    Invoice.objects.all().delete()
    response = team["a"].post(
        "/api/v1/billing/invoices/generate/", {"period": f"{MONTH:%Y-%m}"}, format="json"
    )
    assert response.status_code == 200, response.content
    assert response.json()["response_data"]["created"] == 2
    assert set(Invoice.objects.values_list("unit__property__name", flat=True)) == {"Alpha Court"}


def test_pooled_workspace_money_and_settings_are_admin_only(team):
    a, admin = team["a"], team["admin"]
    for path in (
        "/api/v1/payments/destination/",
        "/api/v1/payments/payouts/",
        "/api/v1/payments/payouts/timing/",
        "/api/v1/payments/withdrawals/",
    ):
        assert a.get(path).status_code == 403, path
        assert admin.get(path).status_code == 200, path
    assert a.get("/api/v1/billing/payment-instructions/").status_code == 200
    blocked = a.post(
        "/api/v1/billing/payment-instructions/",
        {"kind": "bank", "label": "Mine", "details": "Acc 1"},
        format="json",
    )
    assert blocked.status_code == 403
    assert (
        a.patch(
            f"/api/v1/organizations/{team['org'].public_id}/", {"town": "Ndola"}, format="json"
        ).status_code
        in (403, 404)
    )
    assert a.get("/api/v1/notifications/reminders/").status_code == 403


def test_alerts_follow_the_property_scope(team):
    MaintenanceRequest.objects.create(
        organization=team["org"], property=team["beta"], reference="MNT-1", title="Roof"
    )
    assert not any(
        "MNT-1" in item["title"]
        for item in team["a"].get("/api/v1/notifications/").json()["response_data"]["items"]
    )
    assert any(
        "MNT-1" in item["title"]
        for item in team["b"].get("/api/v1/notifications/").json()["response_data"]["items"]
    )


def test_manager_with_nothing_assigned_learns_nothing(team):
    client = team["none"]
    secrets = ("Alpha Court", "Beta Court", "Alice Alpha", "Bob Beta", "Sam Shared")
    for path in (
        "/api/v1/properties/",
        "/api/v1/properties/units/",
        "/api/v1/properties/dashboard/",
        "/api/v1/tenants/",
        "/api/v1/leases/",
        "/api/v1/billing/invoices/",
        "/api/v1/billing/invoices/summary/",
        "/api/v1/billing/payments/",
        "/api/v1/billing/payment-proofs/",
        "/api/v1/billing/opening-balances/",
        "/api/v1/reports/rent-roll/",
        "/api/v1/reports/arrears/",
        "/api/v1/reports/collections/",
        "/api/v1/notifications/",
        "/api/v1/notifications/messages/",
        "/api/v1/notifications/message-recipients/",
        "/api/v1/maintenance/requests/",
        "/api/v1/maintenance/requests/summary/",
        "/api/v1/documents/versions/",
        "/api/v1/documents/originals/",
        "/api/v1/payments/collections/",
    ):
        response = client.get(path)
        assert response.status_code in (200, 403), (path, response.status_code)
        body = response.content.decode()
        assert not any(secret in body for secret in secrets), path


# --- Team administration ---------------------------------------------------------


def invite(client, **overrides):
    payload = {"email": "new.manager@example.com", "full_name": "Nora New", "role": "manager"}
    payload.update(overrides)
    return client.post(f"{TEAM}invitations/", payload, format="json")


def token():
    return re.search(r"token=([A-Za-z0-9_-]+)", mail.outbox[-1].body)[1]


@pytest.fixture
def outbox(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    return mail.outbox


def test_admin_invites_a_manager_who_joins_with_their_properties(team, outbox):
    sent = invite(team["admin"], properties=[str(team["alpha"].public_id)])
    assert sent.status_code == 201, sent.content
    pending = sent.json()["response_data"]["invitations"]
    assert pending[0]["email"] == "new.manager@example.com"
    assert pending[0]["properties"][0]["name"] == "Alpha Court"
    assert len(outbox) == 1 and "property manager" in outbox[0].body

    anonymous = APIClient()
    preview = anonymous.post(
        "/api/v1/accounts/team-invitations/preview/", {"token": token()}, format="json"
    )
    assert preview.status_code == 200, preview.content
    assert preview.json()["response_data"]["workspace_name"] == "Kabulonga Estates"
    weak = anonymous.post(
        "/api/v1/accounts/team-invitations/accept/",
        {"token": token(), "password": "short"},
        format="json",
    )
    assert weak.status_code == 400
    accepted = anonymous.post(
        "/api/v1/accounts/team-invitations/accept/",
        {"token": token(), "password": "A-Long-Passphrase-27"},
        format="json",
    )
    assert accepted.status_code == 200, accepted.content
    user = User.objects.get(email="new.manager@example.com")
    membership = OrganizationMembership.objects.get(user=user)
    assert (membership.role, membership.organization) == (Role.MANAGER, team["org"])
    assert list(membership.property_assignments.values_list("property__name", flat=True)) == [
        "Alpha Court"
    ]
    # Single use.
    again = anonymous.post(
        "/api/v1/accounts/team-invitations/accept/",
        {"token": token(), "password": "A-Long-Passphrase-27"},
        format="json",
    )
    assert again.status_code == 400
    client = APIClient()
    client.force_authenticate(user)
    assert names(client.get("/api/v1/properties/")) == ["Alpha Court"]
    assert AuditEvent.objects.filter(action="team.invitation_accepted").count() == 1


def test_invitation_rules(team, outbox):
    admin = team["admin"]
    # Only an admin invites; a manager cannot grow or promote the team.
    assert invite(team["a"]).status_code == 403
    assert invite(APIClient()).status_code in (401, 403)
    assert invite(team["outsider"], properties=[str(team["alpha"].public_id)]).status_code == 400
    assert invite(admin, role="tenant").status_code == 400
    assert invite(admin, role="platform_admin").status_code == 400
    assert invite(admin, email="not-an-email").status_code == 400
    # A property from another workspace cannot be handed out.
    assert invite(admin, properties=[str(team["foreign"].public_id)]).status_code == 400
    # Someone who already has a Dwella role cannot be invited again.
    assert invite(admin, email="anna@example.com").status_code == 400
    assert invite(admin, email="olga@example.com").status_code == 400
    assert not TeamInvitation.objects.exists() and not outbox

    assert invite(admin).status_code == 201
    first = token()
    assert invite(admin).status_code == 201  # A new invitation replaces the old link.
    stale = APIClient().post(
        "/api/v1/accounts/team-invitations/preview/", {"token": first}, format="json"
    )
    assert stale.status_code == 400
    live = TeamInvitation.objects.get(revoked_at__isnull=True)
    assert team["a"].post(f"{TEAM}invitations/{live.public_id}/revoke/").status_code == 403
    assert admin.post(f"{TEAM}invitations/{live.public_id}/revoke/").status_code == 200
    gone = APIClient().post(
        "/api/v1/accounts/team-invitations/accept/",
        {"token": token(), "password": "A-Long-Passphrase-27"},
        format="json",
    )
    assert gone.status_code == 400
    assert not User.objects.filter(email="new.manager@example.com").exists()


def test_existing_account_must_sign_in_and_tenants_cannot_become_managers(team, outbox):
    spare = User.objects.create_user(
        username="spare@example.com", email="spare@example.com", password="StrongerPass123"
    )
    assert invite(team["admin"], email="spare@example.com", role="landlord").status_code == 201
    anonymous = APIClient().post(
        "/api/v1/accounts/team-invitations/accept/", {"token": token()}, format="json"
    )
    assert anonymous.status_code == 403
    wrong = team["a"].post(
        "/api/v1/accounts/team-invitations/accept/", {"token": token()}, format="json"
    )
    assert wrong.status_code == 403
    # Becoming a tenant somewhere after the invitation was sent blocks acceptance.
    tenant_membership = OrganizationMembership.objects.create(
        organization=team["other"], user=spare, role=Role.TENANT
    )
    client = APIClient()
    client.force_authenticate(spare)
    blocked = client.post(
        "/api/v1/accounts/team-invitations/accept/", {"token": token()}, format="json"
    )
    assert blocked.status_code == 403
    tenant_membership.delete()
    accepted = client.post(
        "/api/v1/accounts/team-invitations/accept/", {"token": token()}, format="json"
    )
    assert accepted.status_code == 200, accepted.content
    assert OrganizationMembership.objects.get(user=spare).role == Role.LANDLORD


def test_admin_changes_assignments_and_access_follows_immediately(team):
    admin, a = team["admin"], team["a"]
    member = f"{TEAM}members/{a.membership.public_id}/"
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court"]
    changed = admin.patch(member, {"properties": [str(team["beta"].public_id)]}, format="json")
    assert changed.status_code == 200, changed.content
    # The same signed-in session loses Alpha and gains Beta on its next request.
    assert names(a.get("/api/v1/properties/")) == ["Beta Court"]
    assert a.get(f"/api/v1/leases/{team['lease_a'].public_id}/").status_code == 404
    event = AuditEvent.objects.get(action="team.member_changed")
    assert event.metadata["properties"] == {"added": ["Beta Court"], "removed": ["Alpha Court"]}

    assert (
        admin.patch(
            member, {"properties": [str(team["foreign"].public_id)]}, format="json"
        ).status_code
        == 400
    )
    assert admin.patch(member, {"role": "tenant"}, format="json").status_code == 400
    promoted = admin.patch(member, {"role": "landlord"}, format="json")
    assert promoted.status_code == 200
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court", "Beta Court"]
    assert not a.membership.property_assignments.exists()


def test_managers_cannot_administer_the_team(team):
    a, b = team["a"], team["b"]
    own = f"{TEAM}members/{a.membership.public_id}/"
    assert a.patch(own, {"role": "landlord"}, format="json").status_code == 403
    assert (
        a.patch(own, {"properties": [str(team["beta"].public_id)]}, format="json").status_code
        == 403
    )
    assert a.delete(f"{TEAM}members/{b.membership.public_id}/").status_code == 403
    assert a.patch(TEAM, {"allow_teammate_cover": False}, format="json").status_code == 403
    # Another workspace's admin cannot reach this team at all.
    outsider = team["outsider"]
    assert outsider.patch(own, {"role": "landlord"}, format="json").status_code == 400
    assert outsider.delete(own).status_code == 400
    a.membership.refresh_from_db()
    assert a.membership.role == Role.MANAGER and a.membership.is_active
    # Teammates see names and properties, not each other's contact details.
    listing = a.get(TEAM).json()["response_data"]
    assert listing["can_manage"] is False and listing["invitations"] == []
    emails = {row["name"]: row["email"] for row in listing["members"]}
    assert emails["Anna"] == "anna@example.com" and emails["Ben"] == ""


def test_workspace_always_keeps_an_admin(team):
    admin = team["admin"]
    own = f"{TEAM}members/{admin.membership.public_id}/"
    assert admin.patch(own, {"role": "manager"}, format="json").status_code == 403
    assert admin.delete(own).status_code == 403

    second = person(team["org"], Role.LANDLORD, "second")
    assert second.delete(own).status_code == 200
    assert admin.get("/api/v1/properties/").status_code == 403
    last = f"{TEAM}members/{second.membership.public_id}/"
    assert second.patch(last, {"role": "manager"}, format="json").status_code == 403
    assert OrganizationMembership.objects.filter(
        organization=team["org"], role=Role.LANDLORD, is_active=True
    ).count() == 1


def test_removed_manager_loses_access_at_once_and_can_be_invited_back(team, outbox):
    admin, a = team["admin"], team["a"]
    removed = admin.delete(f"{TEAM}members/{a.membership.public_id}/")
    assert removed.status_code == 200, removed.content
    assert a.get("/api/v1/properties/").status_code == 403
    assert a.get("/api/v1/tenants/").status_code == 403
    assert not PropertyAssignment.objects.filter(membership=a.membership).exists()
    assert AuditEvent.objects.filter(action="team.member_removed").count() == 1

    back = invite(admin, email="anna@example.com", properties=[str(team["beta"].public_id)])
    assert back.status_code == 201, back.content
    accepted = a.post(
        "/api/v1/accounts/team-invitations/accept/", {"token": token()}, format="json"
    )
    assert accepted.status_code == 200, accepted.content
    assert names(a.get("/api/v1/properties/")) == ["Beta Court"]


# --- Covering for a teammate -----------------------------------------------------


def start_cover(client, teammate, **overrides):
    payload = {
        "teammate": str(teammate.membership.public_id),
        "reason": "Ben is on leave this week",
    }
    payload.update(overrides)
    return client.post(f"{TEAM}cover/", payload, format="json")


def test_manager_covers_a_teammate_and_every_change_is_on_the_record(team):
    a, b = team["a"], team["b"]
    invoice_b = Invoice.objects.get(lease=team["lease_b"])
    invoice_a = Invoice.objects.get(lease=team["lease_a"])
    url_b = f"/api/v1/billing/invoices/{invoice_b.public_id}/record-payment/"
    assert a.post(url_b, {"amount": "50.00", "method": "cash"}, format="json").status_code == 404

    started = start_cover(a, b)
    assert started.status_code == 201, started.content
    assert started.json()["response_data"]["covers"][0]["covering_for"]["name"] == "Ben"
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court", "Beta Court"]

    paid = a.post(url_b, {"amount": "50.00", "method": "cash"}, format="json")
    assert paid.status_code == 201, paid.content
    # The covering manager's own name stays on the payment.
    assert paid.json()["response_data"]["recorded_payment"]["recorded_by_name"] == "Anna"
    event = AuditEvent.objects.get(action="cover.change")
    assert event.actor == a.user
    assert event.metadata["on_behalf_of"] == b.user.pk
    assert event.metadata["on_behalf_of_name"] == "Ben"
    assert event.metadata["reason"] == "Ben is on leave this week"
    assert event.metadata["property_ids"] == [team["beta"].pk]

    # Work on the manager's own property is not attributed to the teammate.
    own = a.post(
        f"/api/v1/billing/invoices/{invoice_a.public_id}/record-payment/",
        {"amount": "50.00", "method": "cash"},
        format="json",
    )
    assert own.status_code == 201
    assert AuditEvent.objects.filter(action="cover.change").count() == 1

    # Both people and the admin can see the trail; an uninvolved manager cannot.
    for key, expected in (("a", 2), ("b", 2), ("admin", 2), ("none", 0)):
        activity = team[key].get(f"{TEAM}activity/").json()["response_data"]
        covers = [row for row in activity if row["action"].startswith("cover.")]
        assert len(covers) == expected, key
    shown = team["b"].get(f"{TEAM}activity/").json()["response_data"][0]
    assert shown["property_names"] == ["Beta Court"] and shown["actor"] == "Anna"
    # The teammate is told in their notifications.
    alerts = b.get("/api/v1/notifications/").json()["response_data"]["items"]
    assert any(item["id"].startswith("cover:") for item in alerts)

    ended = a.delete(f"{TEAM}cover/")
    assert ended.status_code == 200, ended.content
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court"]
    assert a.post(url_b, {"amount": "50.00", "method": "cash"}, format="json").status_code == 404
    assert AuditEvent.objects.filter(action="cover.ended").count() == 1


def test_cover_rules(team):
    a, b, admin = team["a"], team["b"], team["admin"]
    assert start_cover(a, a).status_code == 400
    assert start_cover(a, admin).status_code == 400  # Admins are not covered.
    assert start_cover(admin, b).status_code == 403  # Admins already see everything.
    assert start_cover(a, team["outsider"]).status_code == 400
    assert start_cover(a, b, reason="x").status_code == 400
    assert start_cover(a, b, hours=1000).status_code == 400
    assert start_cover(APIClient(), b).status_code in (401, 403)
    assert not CoverSession.objects.exists()

    assert start_cover(a, b).status_code == 201
    assert start_cover(a, team["both"]).status_code == 400  # One cover at a time.
    # The teammate's own access is unchanged, and a cover does not chain.
    assert names(b.get("/api/v1/properties/")) == ["Beta Court"]
    assert names(team["none"].get("/api/v1/properties/")) == []
    # Covering never unlocks admin-only areas.
    assert a.get("/api/v1/payments/payouts/").status_code == 403
    assert a.post(f"{TEAM}invitations/", {}, format="json").status_code == 403


def test_cover_shrinks_expires_and_can_be_stopped_by_an_admin(team):
    a, b, admin = team["a"], team["b"], team["admin"]
    assert start_cover(a, b).status_code == 201
    cover = CoverSession.objects.get()
    # Changing the teammate's properties changes the cover with it.
    admin.patch(f"{TEAM}members/{b.membership.public_id}/", {"properties": []}, format="json")
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court"]
    admin.patch(
        f"{TEAM}members/{b.membership.public_id}/",
        {"properties": [str(team["beta"].public_id)]},
        format="json",
    )
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court", "Beta Court"]

    assert b.delete(f"{TEAM}cover/{cover.public_id}/").status_code == 400  # Not theirs to end.
    assert admin.delete(f"{TEAM}cover/{cover.public_id}/").status_code == 200
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court"]

    assert start_cover(a, b).status_code == 201
    CoverSession.objects.filter(ended_at__isnull=True).update(
        expires_at=timezone.now() - timedelta(minutes=1)
    )
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court"]
    assert start_cover(a, b).status_code == 201  # An expired cover does not block a new one.

    off = admin.patch(TEAM, {"allow_teammate_cover": False}, format="json")
    assert off.status_code == 200 and off.json()["response_data"]["covers"] == []
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court"]
    assert start_cover(a, b).status_code == 403
    # Removing the covered teammate ends covers made for them.
    admin.patch(TEAM, {"allow_teammate_cover": True}, format="json")
    assert start_cover(a, b).status_code == 201
    assert admin.delete(f"{TEAM}members/{b.membership.public_id}/").status_code == 200
    assert names(a.get("/api/v1/properties/")) == ["Alpha Court"]
    assert not CoverSession.objects.filter(ended_at__isnull=True).exists()


# --- Other channels and background work ------------------------------------------


def test_queued_message_is_stopped_when_the_assignment_is_removed(team):
    from apps.notifications.messaging import actor_allowed

    a, tenant = team["a"], team["lease_a"].tenant
    assert actor_allowed(team["org"], a.user, tenant)
    assert not actor_allowed(team["org"], a.user, team["lease_b"].tenant)
    assert actor_allowed(team["org"], team["admin"].user, team["lease_b"].tenant)
    a.membership.property_assignments.all().delete()
    assert not actor_allowed(team["org"], a.user, tenant)


def test_message_recipients_and_all_tenants_stay_inside_scope(team):
    from apps.common.property_scope import scope_for_membership
    from apps.notifications.messaging import preview

    scope = scope_for_membership(team["a"].membership)
    message = preview(
        organization=team["org"],
        actor=team["a"].user,
        data={"channel": "email", "all_tenants": True, "subject": "Water", "body": "Off at 9"},
        scope=scope,
    )
    assert sorted(row["name"] for row in message.recipients) == ["Alice Alpha", "Sam Shared"]
    listed = names(team["a"].get("/api/v1/notifications/message-recipients/"), "full_name")
    assert listed == ["Alice Alpha", "Sam Shared"]
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError):
        preview(
            organization=team["org"],
            actor=team["a"].user,
            data={
                "channel": "email",
                "tenants": [team["lease_b"].tenant.public_id],
                "subject": "Hi",
                "body": "Hello",
            },
            scope=scope,
        )


def test_notices_and_signing_reach_the_right_managers(team):
    from apps.common.property_scope import management_members
    from apps.documents.services import active_signer

    def who(property_obj):
        return sorted(
            management_members(team["org"].pk, [property_obj.pk]).values_list(
                "user__first_name", flat=True
            )
        )

    assert who(team["alpha"]) == ["Admin", "Anna", "Bola"]
    assert who(team["beta"]) == ["Admin", "Ben", "Bola"]
    assert sorted(
        management_members(team["org"].pk).values_list("user__first_name", flat=True)
    ) == ["Admin"]

    assert active_signer(team["admin"].user, team["org"], team["lease_b"])
    assert active_signer(team["a"].user, team["org"], team["lease_a"])
    assert not active_signer(team["a"].user, team["org"], team["lease_b"])
    assert not active_signer(team["none"].user, team["org"], team["lease_a"])
    signers = team["a"].get("/api/v1/documents/versions/signers/").json()["response_data"]
    assert sorted(row["name"] for row in signers) == ["Admin", "Anna"]


def test_assistant_and_whatsapp_stay_closed_to_assigned_managers(team, settings):
    from rest_framework.exceptions import PermissionDenied

    from apps.accounts.access_state import mark_email_verified
    from apps.accounts.handy_agent import token_access
    from apps.notifications.whatsapp.access import memberships

    with pytest.raises(PermissionDenied):
        token_access(team["a"].user, None)
    mark_email_verified(team["a"].user)
    mark_email_verified(team["admin"].user)
    assert not memberships(team["a"].user).exists()
    assert memberships(team["admin"].user).exists()


def test_scope_adds_a_fixed_number_of_queries_not_one_per_row(team, django_assert_max_num_queries):
    a = team["a"]
    with django_assert_max_num_queries(40) as small:
        a.get("/api/v1/tenants/")
    for index in range(12):
        phone = f"+2609711{index:05d}"
        tenancy(team["org"], team["alpha"], f"A{index + 10}", f"Extra {index}", phone)
    with django_assert_max_num_queries(40) as full:
        assert len(rows(a.get("/api/v1/tenants/"))) == 14
    assert len(full.captured_queries) <= len(small.captured_queries) + 1
