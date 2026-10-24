from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.billing.tests import make_lease
from apps.documents.models import DocumentVersion
from apps.documents.tests import prepare, sign_payload, verified
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit

from .catalog import Feature, Resource
from .models import WorkspaceAccessPolicy
from .services import capacity_guard, feature_state, require_feature

pytestmark = pytest.mark.django_db
URL = "/api/v1/subscriptions/entitlements/"


def actor(org, name="manager", role="landlord", **flags):
    user = get_user_model().objects.create_user(
        username=name, email=f"{name}@example.com", first_name="Manager", **flags
    )
    if org:
        OrganizationMembership.objects.create(organization=org, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return user, client


@pytest.fixture(autouse=True)
def isolated(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def env():
    org = Organization.objects.create(name="Access test workspace")
    user, client = actor(org)
    prop = Property.objects.create(organization=org, name="Home", address="Plot 12")
    return org, user, client, prop


def admin_path(org):
    return f"/api/v1/platform/workspaces/{org.public_id}/entitlements/"


def test_beta_defaults_are_open_unlimited_and_read_only(env):
    org, _, client, _ = env
    response = client.get(URL)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    data = response.json()["response_data"]
    assert data["organization_id"] == str(org.public_id)
    assert all(value["enabled"] for value in data["features"].values())
    assert all(value["limit"] is None for value in data["limits"].values())
    assert data["limits"]["properties"]["used"] == 1
    assert not WorkspaceAccessPolicy.objects.exists()
    assert client.patch(URL, {"limits": {"units": 100}}, format="json").status_code == 405


@pytest.mark.parametrize("kind", ["anonymous", "manager", "tenant", "staff"])
def test_only_platform_superuser_can_manage_policies(env, kind):
    org, _, client, _ = env
    if kind == "anonymous":
        client = APIClient()
    elif kind == "tenant":
        _, client = actor(org, "tenant", "tenant")
    elif kind == "staff":
        _, client = actor(None, "support", is_staff=True)
    path = admin_path(org)
    assert client.get(path).status_code == 403
    assert client.patch(path, {"limits": {"units": 0}}, format="json").status_code == 403
    assert not WorkspaceAccessPolicy.objects.exists()


def test_workspace_scope_and_role_permissions_still_apply(env):
    org, _, client, _ = env
    other = Organization.objects.create(name="Other private workspace")
    WorkspaceAccessPolicy.objects.create(organization=other, limits={"units": 123})
    client.credentials(HTTP_X_DWELLA_WORKSPACE=str(other.public_id))
    assert client.get(URL).json()["response_data"]["limits"]["units"]["limit"] is None
    assert client.get(URL).json()["response_data"]["organization_id"] == str(org.public_id)
    _, tenant = actor(org, "tenant", "tenant")
    assert tenant.get(URL).status_code == 403
    assert APIClient().get(URL).status_code == 403
    org.is_active = False
    org.save()
    assert client.get(URL).status_code == 403
    with pytest.raises(PermissionDenied):
        require_feature(org, Feature.BULK_IMPORTS)


def test_patch_merges_resets_and_audits_without_exposing_billing_identifiers(env):
    org, _, manager, _ = env
    admin, client = actor(None, "platform", is_superuser=True)
    path = admin_path(org)
    assert (
        client.patch(
            path,
            {"limits": {"units": 2}, "feature_overrides": {"bulk_imports": {"enabled": False}}},
            format="json",
        ).status_code
        == 200
    )
    assert client.patch(path, {"limits": {"tenants": 10}}, format="json").status_code == 200
    policy = WorkspaceAccessPolicy.objects.get()
    assert policy.limits == {"units": 2, "tenants": 10}
    assert not manager.get(URL).json()["response_data"]["features"]["bulk_imports"]["enabled"]
    with pytest.raises(PermissionDenied):
        require_feature(org, Feature.BULK_IMPORTS)
    assert (
        client.patch(
            path,
            {"feature_overrides": {"bulk_imports": None}, "limits": {"units": None}},
            format="json",
        ).status_code
        == 200
    )
    require_feature(org, Feature.BULK_IMPORTS)
    assert manager.get(URL).json()["response_data"]["limits"]["units"]["limit"] is None
    assert (
        AuditEvent.objects.filter(action="subscription.access_policy_updated", actor=admin).count()
        == 3
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"plan": "premium"},
        {"organization_id": "other", "limits": {}},
        {"feature_overrides": {"unknown": {"enabled": True}}},
        {"feature_overrides": {"bulk_imports": {"enabled": "invalid"}}},
        {"feature_overrides": {"bulk_imports": {"enabled": True, "expiry_typo": "2030"}}},
        {"feature_overrides": {"bulk_imports": {"enabled": True, "expires_at": "bad"}}},
        {"limits": {"unknown": 1}},
        {"limits": {"units": -1}},
        {"limits": {"units": True}},
        {"limits": {"units": 1.5}},
        {"limits": {"units": 2_147_483_648}},
        {"limits": []},
    ],
)
def test_policy_validation_is_authoritative_and_atomic(env, payload):
    org, _, _, _ = env
    _, client = actor(None, "platform", is_superuser=True)
    assert client.patch(admin_path(org), payload, format="json").status_code == 400
    assert not WorkspaceAccessPolicy.objects.exists()
    assert not AuditEvent.objects.filter(action="subscription.access_policy_updated").exists()


def test_expiring_grants_and_invalid_internal_policy_fail_closed(env):
    org = env[0]
    policy = WorkspaceAccessPolicy.objects.create(
        organization=org,
        feature_overrides={
            "bulk_imports": {
                "enabled": True,
                "expires_at": (timezone.now() - timedelta(seconds=1)).isoformat(),
            }
        },
    )
    assert feature_state(policy, Feature.BULK_IMPORTS)["reason"] == "expired"
    with pytest.raises(PermissionDenied):
        require_feature(org, Feature.BULK_IMPORTS)
    for invalid in [
        {"enabled": "true"},
        {"enabled": True, "expires_at": "bad"},
        {"enabled": True, "expires_at": False},
        False,
    ]:
        policy.feature_overrides = {"bulk_imports": invalid}
        policy.save()
        assert not feature_state(policy, Feature.BULK_IMPORTS)["enabled"]
    with pytest.raises(ValueError):
        require_feature(org, "typo")


def test_unit_limit_is_enforced_on_create_but_keeps_existing_records_editable(env):
    org, _, client, prop = env
    WorkspaceAccessPolicy.objects.create(organization=org, limits={"units": 1})
    payload = {"property": str(prop.public_id), "name": "A1", "rent_amount": "1000"}
    first = client.post("/api/v1/properties/units/", payload, format="json")
    assert first.status_code == 201, first.content
    blocked = client.post("/api/v1/properties/units/", {**payload, "name": "A2"}, format="json")
    assert blocked.status_code == 403
    assert blocked.json()["response_data"]["code"] == "capacity_exceeded"
    policy = WorkspaceAccessPolicy.objects.get()
    policy.limits = {"units": 0}
    policy.save()
    unit = Unit.objects.get()
    assert client.get(f"/api/v1/properties/units/{unit.public_id}/").status_code == 200
    assert (
        client.patch(
            f"/api/v1/properties/units/{unit.public_id}/",
            {"notes": "History remains available"},
            format="json",
        ).status_code
        == 200
    )
    assert Unit.objects.count() == 1


def test_property_tenant_and_setup_cannot_bypass_limits(env):
    org, _, client, _ = env
    WorkspaceAccessPolicy.objects.create(organization=org, limits={"properties": 1, "tenants": 0})
    assert (
        client.post(
            "/api/v1/properties/",
            {"name": "Blocked", "property_type": "house", "address": "Plot 2"},
            format="json",
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/tenants/",
            {"full_name": "New Tenant", "phone_number": "0971234567"},
            format="json",
        ).status_code
        == 403
    )
    from apps.tenants.models import Tenant

    assert not Tenant.objects.exists()
    other = Organization.objects.create(name="Empty owner")
    _, owner = actor(other, "emptyowner")
    WorkspaceAccessPolicy.objects.create(organization=other, limits={"units": 0})
    response = owner.post(
        "/api/v1/organizations/onboarding/",
        {
            "business_name": "Changed",
            "property_name": "Blocked setup",
            "property_type": "house",
            "address": "Plot 9",
            "unit_name": "U1",
            "rent_amount": "1000",
        },
        format="json",
    )
    assert response.status_code == 403, response.content
    assert not Property.objects.filter(organization=other).exists()
    other.refresh_from_db()
    assert other.display_name == ""


def test_assistant_uses_the_same_unit_limit(env):
    from apps.assistant.test_actions import JWT_SETTINGS, client_for
    from apps.audit.models import PlatformSettings

    org, user, _, prop = env
    WorkspaceAccessPolicy.objects.create(organization=org, limits={"units": 0})
    PlatformSettings.objects.create(pk=1, handy_agent_enabled=True)
    with JWT_SETTINGS:
        client = client_for(user, org)
        response = client.post(
            "/api/v1/assistant/units/",
            {"property": str(prop.public_id), "name": "Blocked", "rent_amount": "1000"},
            format="json",
        )
    assert response.status_code == 403, response.content
    assert not Unit.objects.exists()


def test_batch_guard_rolls_back_oversized_imports_and_validates_actual_growth(env):
    org, _, _, prop = env
    WorkspaceAccessPolicy.objects.create(organization=org, limits={"units": 1})
    with pytest.raises(PermissionDenied):
        with capacity_guard(org, Resource.UNITS, additional=2):
            pytest.fail("Over-limit batch must not start")
    with pytest.raises(PermissionDenied):
        with capacity_guard(org, Resource.UNITS, additional=1):
            Unit.objects.create(organization=org, property=prop, name="A1", rent_amount=1000)
            Unit.objects.create(organization=org, property=prop, name="A2", rent_amount=1000)
    assert not Unit.objects.exists()
    with capacity_guard(org, Resource.UNITS):
        Unit.objects.create(organization=org, property=prop, name="A1", rent_amount=1000)
    assert Unit.objects.count() == 1
    with pytest.raises(ValueError):
        with capacity_guard(org, Resource.UNITS, additional=-1):
            pytest.fail("Negative growth must be rejected")


def test_new_document_work_can_be_gated_without_locking_existing_signers_out(env):
    org, user, client, _ = env
    lease = make_lease(org, active=False)
    lease.tenant.email = "tenant@example.com"
    lease.tenant.save()
    setup = (org, user, client, lease)
    doc = prepare(setup)
    public, _, url = verified(client, doc)
    WorkspaceAccessPolicy.objects.update_or_create(
        organization=org,
        defaults={
            "feature_overrides": {
                "lease_documents": {"enabled": False},
                "lease_signing": {"enabled": False},
            }
        },
    )
    assert client.post(f"/api/v1/documents/versions/{doc['id']}/invite/", {}).status_code == 403
    assert client.get(f"/api/v1/documents/versions/{doc['id']}/pdf/").status_code == 200
    assert public.get(url + "document/").status_code == 200
    assert public.post(url + "sign/", sign_payload(doc, lease.tenant.full_name)).status_code == 200
    assert (
        client.post(
            "/api/v1/documents/versions/",
            {
                "lease": str(lease.public_id),
                "landlord_name": "Owner",
                "landlord_address": "Lusaka",
                "agreement_text": "Approved agreement. " * 20,
                "terms_approved": True,
            },
            format="json",
        ).status_code
        == 403
    )
    assert DocumentVersion.objects.count() == 1


def test_policy_writes_roll_back_if_audit_fails_and_are_throttled(env):
    org = env[0]
    _, client = actor(None, "platform", is_superuser=True)
    with patch("apps.subscriptions.views.record_event", side_effect=RuntimeError("Audit down")):
        with pytest.raises(RuntimeError):
            client.patch(admin_path(org), {"limits": {"units": 0}}, format="json")
    assert not WorkspaceAccessPolicy.objects.exists()
    cache.clear()
    for _ in range(30):
        assert client.patch(admin_path(org), {"limits": {}}, format="json").status_code == 200
    assert client.patch(admin_path(org), {"limits": {}}, format="json").status_code == 429


def test_session_authenticated_policy_writes_require_csrf(env):
    user, _ = actor(None, "platform", is_superuser=True)
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    assert (
        client.patch(admin_path(env[0]), {"limits": {"units": 0}}, format="json").status_code == 403
    )
    assert not WorkspaceAccessPolicy.objects.exists()


def test_feature_mixin_adds_checks_after_existing_role_permissions(env):
    from rest_framework.response import Response
    from rest_framework.test import APIRequestFactory, force_authenticate
    from rest_framework.views import APIView

    from apps.common.permissions import CanManagePortfolio

    from .permissions import FeatureAccessMixin

    org, user, _, _ = env

    class ExampleAction(FeatureAccessMixin, APIView):
        permission_classes = [CanManagePortfolio]
        required_feature = Feature.BULK_IMPORTS

        def get_organization(self):
            return org

        def post(self, request):
            return Response({"done": True})

    def perform(who):
        request = APIRequestFactory().post("/api/v1/properties/example/")
        force_authenticate(request, user=who)
        return ExampleAction.as_view()(request)

    assert perform(user).status_code == 200
    WorkspaceAccessPolicy.objects.create(
        organization=org, feature_overrides={"bulk_imports": {"enabled": False}}
    )
    assert perform(user).status_code == 403
    tenant, _ = actor(org, "tenant", "tenant")
    WorkspaceAccessPolicy.objects.filter(organization=org).delete()
    assert perform(tenant).status_code == 403


def test_suspended_workspace_and_invalid_capacity_policy_fail_closed(env):
    org, _, client, prop = env
    policy = WorkspaceAccessPolicy.objects.create(organization=org, limits={"units": True})
    with pytest.raises(PermissionDenied):
        with capacity_guard(org, Resource.UNITS):
            pytest.fail("Malformed capacity must not grant unlimited access")
    policy.limits = {}
    policy.save()
    org.is_active = False
    org.save()
    with pytest.raises(PermissionDenied):
        with capacity_guard(org, Resource.UNITS):
            pytest.fail("Suspended workspaces cannot add records")
    assert (
        client.post(
            "/api/v1/properties/units/",
            {"property": str(prop.public_id), "name": "Blocked", "rent_amount": "1000"},
            format="json",
        ).status_code
        == 403
    )


@pytest.mark.django_db(transaction=True)
def test_competing_creates_cannot_exceed_one_available_unit_slot(env):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connection

    if connection.vendor != "postgresql":
        pytest.skip("Requires real row locks")
    org, user, _, prop = env
    WorkspaceAccessPolicy.objects.create(organization=org, limits={"units": 1})
    barrier = Barrier(2)

    def create(name):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user=user)
            barrier.wait(timeout=10)
            return client.post(
                "/api/v1/properties/units/",
                {"property": str(prop.public_id), "name": name, "rent_amount": "1000"},
                format="json",
            ).status_code
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create, name) for name in ["A1", "A2"]]
        assert sorted(f.result(timeout=20) for f in futures) == [201, 403]
    assert Unit.objects.count() == 1
