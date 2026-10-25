from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.organizations.models import Organization, OrganizationMembership

from .models import Destination
from .testing import checkout, client_for

pytestmark = pytest.mark.django_db
URL = "/api/v1/payments/destination/"
DETAILS = {
    "phone": "0972222222",
    "operator": "mtn",
    "account_name": "Test receiver",
    "confirm_details": True,
}


@pytest.fixture(autouse=True)
def test_setup(settings):
    settings.APP_ENVIRONMENT = "test"
    settings.LENCO_ALLOW_UNVERIFIED_DESTINATIONS = True


def test_manager_saves_without_admin_and_preserves_started_payments(home):
    original = home["destination"]
    collection = checkout(home)
    client = client_for(home["manager"])
    with patch("apps.payments.provider.urllib.request.build_opener") as network:
        response = client.post(URL, DETAILS, format="json")
        assert response.status_code == 200
        assert response.json()["response_data"]["phone"] == "+260972222222"
        assert client.post(URL, DETAILS, format="json").status_code == 200
        network.assert_not_called()
    assert Destination.objects.filter(organization=home["org"]).count() == 2
    active = Destination.objects.get(organization=home["org"], enabled=True)
    assert active.approved_by == home["manager"]
    original.refresh_from_db()
    collection.refresh_from_db()
    assert not original.enabled and collection.destination_id == original.pk
    assert AuditEvent.objects.filter(action="payment.destination_saved").exists()
    payload = client.get(URL).json()["response_data"]
    assert (
        payload["self_service_enabled"] is True and payload["phone_verification_enabled"] is False
    )


@pytest.mark.parametrize(
    "environment,allowed",
    [("production", True), ("production", False), ("test", False), ("staging", True)],
)
def test_verification_bypass_is_test_only(home, settings, environment, allowed):
    settings.APP_ENVIRONMENT = environment
    settings.LENCO_ALLOW_UNVERIFIED_DESTINATIONS = allowed
    client = client_for(home["manager"])
    assert client.post(URL, DETAILS, format="json").status_code == 400
    assert client.get(URL).json()["response_data"]["self_service_enabled"] is False
    assert Destination.objects.filter(organization=home["org"]).count() == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"phone": "bad"},
        {"phone": "+441234567890"},
        {"operator": "other"},
        {"account_name": ""},
        {"confirm_details": False},
        {"confirm_details": None},
    ],
)
def test_bad_input_cannot_replace_the_destination(home, changes):
    response = client_for(home["manager"]).post(URL, {**DETAILS, **changes}, format="json")
    assert response.status_code == 400
    assert Destination.objects.get(organization=home["org"], enabled=True) == home["destination"]


def test_access_is_scoped_and_tenant_and_admin_cannot_save(home):
    assert APIClient().post(URL, DETAILS, format="json").status_code in (401, 403)
    for user in (home["tenant"], home["admin"]):
        assert client_for(user).post(URL, DETAILS, format="json").status_code == 403
    other = Organization.objects.create(name="Separate receiving workspace")
    manager = get_user_model().objects.create_user(username="other-destination-manager")
    OrganizationMembership.objects.create(organization=other, user=manager, role="landlord")
    response = client_for(manager).post(
        URL, {**DETAILS, "organization_id": str(home["org"].public_id)}, format="json"
    )
    assert response.status_code == 200
    assert Destination.objects.get(organization=home["org"], enabled=True) == home["destination"]
    assert Destination.objects.get(organization=other, enabled=True).approved_by == manager


def test_currency_suspension_and_revocation_are_enforced(home):
    client = client_for(home["manager"])
    org = home["org"]
    org.currency = "USD"
    org.save()
    assert client.post(URL, DETAILS, format="json").status_code == 400
    org.currency, org.is_active = "ZMW", False
    org.save()
    assert client.post(URL, DETAILS, format="json").status_code == 403
    org.is_active = True
    org.save()
    OrganizationMembership.objects.filter(user=home["manager"]).update(is_active=False)
    assert client.post(URL, DETAILS, format="json").status_code == 403


def test_destination_writes_are_throttled(home):
    from .views import PaymentWriteThrottle

    cache.clear()
    with patch.object(PaymentWriteThrottle, "rate", "1/hour"):
        client = client_for(home["manager"])
        assert client.post(URL, DETAILS, format="json").status_code == 200
        assert client.post(URL, DETAILS, format="json").status_code == 429
