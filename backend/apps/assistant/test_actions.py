from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone
from drf_spectacular.generators import SchemaGenerator
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.accounts.models import HandyActionExecution
from apps.audit.models import AuditEvent
from apps.billing.models import Invoice, Payment
from apps.billing.services import create_invoice
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceRequest, MaintenanceUpdate, Vendor
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, PropertyOwner, Unit
from apps.tenants.models import Tenant

User = get_user_model()
SECRET = "test-handy-agent-action-secret-with-32-characters"
JWT_SETTINGS = override_settings(
    HANDY_AGENT_SIGNING_SECRET=SECRET,
    HANDY_AGENT_ISSUER="https://api.dwella.properties",
    HANDY_AGENT_AUDIENCE="handy-agent",
)


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()


def workspace_user(role="owner"):
    user = User.objects.create_user(
        username=f"{role}-{uuid4()}@example.com",
        email=f"{role}-{uuid4()}@example.com",
        password="StrongerPass123",
    )
    organization = Organization.objects.create(name=f"Portfolio {uuid4()}")
    membership = OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=role,
    )
    return user, organization, membership


def action_token(user, organization, *, actor=True, expires_in=900, secret=SECRET):
    now = timezone.now()
    return jwt.encode(
        {
            "sub": str(user.pk),
            "name": user.email,
            "groups": ["portfolio_manager", "portfolio_viewer"],
            "agent": {"thinker": True, "actor": actor, "ledger": False},
            "attrs": {"organization_ids": [organization.pk]},
            "aud": "handy-agent",
            "iss": "https://api.dwella.properties",
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
            "jti": str(uuid4()),
        },
        secret,
        algorithm="HS256",
    )


def client_for(user, organization, **token_options):
    client = APIClient()
    token = action_token(user, organization, **token_options)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
@JWT_SETTINGS
def test_owner_can_create_each_approved_resource_end_to_end():
    user, organization, _ = workspace_user()
    client = client_for(user, organization)

    assert client.post(
        "/api/v1/assistant/property-owners/",
        {"full_name": "Chanda Banda", "phone_number": "+260971111111"},
        format="json",
    ).status_code == 201
    owner = PropertyOwner.objects.get(organization=organization)

    assert client.post(
        "/api/v1/assistant/properties/",
        {
            "owner": str(owner.public_id),
            "name": "Kabulonga Heights",
            "property_type": "apartment",
            "management_status": "managed",
            "address": "12 Kabulonga Road",
            "town": "Lusaka",
        },
        format="json",
    ).status_code == 201
    prop = Property.objects.get(organization=organization)

    assert client.post(
        "/api/v1/assistant/units/",
        {
            "property": str(prop.public_id),
            "name": "A1",
            "bedrooms": 2,
            "bathrooms": "1.0",
            "rent_amount": "6500.00",
            "occupancy_status": "vacant",
        },
        format="json",
    ).status_code == 201
    unit = Unit.objects.get(organization=organization)

    assert client.post(
        "/api/v1/assistant/tenants/",
        {
            "full_name": "Mwila Phiri",
            "phone_number": "097 222 3344",
            "email": "mwila@example.com",
        },
        format="json",
    ).status_code == 201
    tenant = Tenant.objects.get(organization=organization)

    assert client.post(
        "/api/v1/assistant/draft-leases/",
        {
            "tenant": str(tenant.public_id),
            "unit": str(unit.public_id),
            "start_date": "2026-11-01",
            "end_date": "2027-10-31",
            "monthly_rent": "6500.00",
            "deposit_amount": "6500.00",
            "rent_due_day": 1,
        },
        format="json",
    ).status_code == 201
    lease = Lease.objects.get(organization=organization)
    assert lease.status == Lease.Status.DRAFT

    assert client.post(
        "/api/v1/assistant/invoices/",
        {
            "tenant": str(tenant.public_id),
            "lease": str(lease.public_id),
            "issue_date": "2026-11-01",
            "due_date": "2026-11-05",
            "lines": [
                {"kind": "rent", "description": "November rent", "amount": "6500.00"}
            ],
            "notes": "Created with tenant approval.",
        },
        format="json",
    ).status_code == 201
    invoice = Invoice.objects.get(organization=organization)

    assert client.post(
        f"/api/v1/assistant/invoices/{invoice.public_id}/payments/",
        {
            "amount": "3000.00",
            "method": "mobile_money",
            "paid_on": "2026-10-23",
            "reference": "MM-123",
        },
        format="json",
    ).status_code == 201

    assert client.post(
        "/api/v1/assistant/vendors/",
        {"name": "Reliable Plumbing", "trade": "Plumbing", "phone_number": "+260955111222"},
        format="json",
    ).status_code == 201

    assert client.post(
        "/api/v1/assistant/maintenance-requests/",
        {
            "property": str(prop.public_id),
            "unit": str(unit.public_id),
            "tenant": str(tenant.public_id),
            "title": "Kitchen tap is leaking",
            "description": "Leak under the sink.",
            "category": "plumbing",
            "priority": "normal",
        },
        format="json",
    ).status_code == 201
    maintenance_request = MaintenanceRequest.objects.get(organization=organization)

    assert client.post(
        f"/api/v1/assistant/maintenance-requests/{maintenance_request.public_id}/comments/",
        {"body": "Tenant is available after 14:00.", "is_internal": False},
        format="json",
    ).status_code == 201

    assert Payment.objects.filter(organization=organization).count() == 1
    assert Vendor.objects.filter(organization=organization).count() == 1
    assert MaintenanceUpdate.objects.filter(
        request=maintenance_request, kind=MaintenanceUpdate.Kind.COMMENT
    ).count() == 1
    assert HandyActionExecution.objects.filter(organization=organization).count() == 10
    assert AuditEvent.objects.filter(
        organization=organization, action__startswith="assistant."
    ).count() == 10


@pytest.mark.django_db
@JWT_SETTINGS
def test_retried_payment_returns_original_receipt_without_duplicate():
    user, organization, _ = workspace_user()
    tenant = Tenant.objects.create(
        organization=organization, full_name="Tenant", phone_number="+260971234567"
    )
    invoice = create_invoice(
        organization=organization,
        tenant=tenant,
        issue_date="2026-10-20",
        due_date="2026-10-30",
        lines=[{"kind": "other", "description": "Test charge", "amount": "500.00"}],
    )
    client = client_for(user, organization)
    payload = {"amount": "200.00", "method": "cash", "paid_on": "2026-10-23"}
    url = f"/api/v1/assistant/invoices/{invoice.public_id}/payments/"

    first = client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="payment-test-1")
    second = client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="payment-test-1")

    assert first.status_code == second.status_code == 201
    assert first.data["receipt_number"] == second.data["receipt_number"]
    assert Payment.objects.filter(invoice=invoice).count() == 1


@pytest.mark.django_db
@JWT_SETTINGS
def test_rejects_reused_idempotency_key_with_different_payload():
    user, organization, _ = workspace_user()
    client = client_for(user, organization)
    headers = {"HTTP_IDEMPOTENCY_KEY": "property-owner-test"}

    assert client.post(
        "/api/v1/assistant/property-owners/",
        {"full_name": "First Owner"},
        format="json",
        **headers,
    ).status_code == 201
    response = client.post(
        "/api/v1/assistant/property-owners/",
        {"full_name": "Different Owner"},
        format="json",
        **headers,
    )

    assert response.status_code == 409
    assert PropertyOwner.objects.filter(organization=organization).count() == 1


@pytest.mark.django_db
@JWT_SETTINGS
@pytest.mark.parametrize(
    "client_factory",
    [
        lambda user, org: APIClient(),
        lambda user, org: client_for(user, org, actor=False),
        lambda user, org: client_for(user, org, expires_in=-1),
        lambda user, org: client_for(user, org, secret="wrong-secret-with-more-than-32-characters"),
    ],
)
def test_rejects_missing_non_actor_expired_and_bad_signature_tokens(client_factory):
    user, organization, _ = workspace_user()
    response = client_factory(user, organization).post(
        "/api/v1/assistant/properties/",
        {"name": "Blocked", "property_type": "house", "address": "Nowhere"},
        format="json",
    )
    assert response.status_code in {401, 403}
    assert not Property.objects.exists()


@pytest.mark.django_db
@JWT_SETTINGS
def test_live_role_demotion_revokes_existing_actor_token():
    user, organization, membership = workspace_user("manager")
    client = client_for(user, organization)
    membership.role = OrganizationMembership.Role.VIEWER
    membership.save(update_fields=["role"])

    response = client.post(
        "/api/v1/assistant/properties/",
        {"name": "Blocked", "property_type": "house", "address": "Nowhere"},
        format="json",
    )
    assert response.status_code in {401, 403}


@pytest.mark.django_db
@JWT_SETTINGS
def test_cross_workspace_references_are_rejected():
    user, organization, _ = workspace_user()
    other = Organization.objects.create(name="Other Portfolio")
    other_property = Property.objects.create(
        organization=other,
        name="Other House",
        property_type="house",
        address="Other Road",
    )

    response = client_for(user, organization).post(
        "/api/v1/assistant/units/",
        {
            "property": str(other_property.public_id),
            "name": "A1",
            "rent_amount": "1000.00",
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Unit.objects.exists()


@pytest.mark.django_db
@JWT_SETTINGS
def test_handy_token_cannot_use_normal_crud_endpoint():
    user, organization, _ = workspace_user()
    response = client_for(user, organization).post(
        "/api/v1/properties/",
        {"name": "Blocked", "property_type": "house", "address": "Nowhere"},
        format="json",
    )
    assert response.status_code in {401, 403}
    assert not Property.objects.exists()


@pytest.mark.django_db
@JWT_SETTINGS
def test_rate_limits_assistant_actions(monkeypatch):
    monkeypatch.setitem(ScopedRateThrottle.THROTTLE_RATES, "handy_agent_action", "1/hour")
    user, organization, _ = workspace_user()
    client = client_for(user, organization)

    assert client.post(
        "/api/v1/assistant/property-owners/",
        {"full_name": "First Owner"},
        format="json",
    ).status_code == 201
    assert client.post(
        "/api/v1/assistant/property-owners/",
        {"full_name": "Second Owner"},
        format="json",
    ).status_code == 429


@pytest.mark.django_db
@JWT_SETTINGS
def test_openapi_marks_only_post_operations_in_assistant_namespace():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    assistant_paths = {
        path: operations
        for path, operations in schema["paths"].items()
        if path.startswith("/api/v1/assistant/")
    }

    assert len(assistant_paths) == 10
    for operations in assistant_paths.values():
        assert set(operations) == {"post"}
        assert operations["post"]["x-agent"] == {"enabled": True}
        assert operations["post"]["security"] == [{"HandyAgentBearer": []}]
