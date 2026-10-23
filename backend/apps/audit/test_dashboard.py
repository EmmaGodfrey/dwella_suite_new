from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import IdentityVerification
from apps.billing.models import Invoice, Payment
from apps.billing.tests import make_lease
from apps.marketing.models import BetaApplication
from apps.properties.models import Property, Unit

from .models import SupportSession

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/dashboard/"


def test_platform_dashboard_aggregates_and_month_boundaries(context):
    client, admin, org, other = context
    now = timezone.now()
    today = timezone.localdate()
    other.is_active = False
    other.save()
    IdentityVerification.objects.create(user=admin, status="pending")
    BetaApplication.objects.create(name="Synthetic applicant", phone="000", role="agent", units="1")
    for ended, expires in [(None, now + timedelta(hours=1)), (now, now + timedelta(hours=1)),
                           (None, now - timedelta(seconds=1))]:
        SupportSession.objects.create(admin=admin, organization=org, reason="Dashboard check",
                                      ended_at=ended, expires_at=expires)
    lease = make_lease(org)
    invoice = Invoice.objects.create(organization=org, tenant=lease.tenant, lease=lease,
        reference="SUMMARY", total=100, issue_date=today, due_date=today)
    for index, (paid_on, reversed_at, amount) in enumerate([
        (today, None, 25), (today, now, 50),
        (today.replace(day=1) - timedelta(days=1), None, 60),
        (today + timedelta(days=1), None, 70),
    ]):
        Payment.objects.create(organization=org, tenant=lease.tenant, invoice=invoice,
            receipt_number=f"SUMMARY-{index}", amount=amount, method="cash", paid_on=paid_on,
            reversed_at=reversed_at)
    client.credentials(HTTP_X_DWELLA_WORKSPACE="stale-context")
    response = client.get(URL)
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data == {
        "workspaces": {"active": 1, "suspended": 1, "new_this_week": 2},
        "users": {"total": 1, "active": 1}, "beta_signups": [{"status": "new", "count": 1}],
        "open_support_sessions": 1, "pending_identity_checks": 1,
        "collections_this_month": "25.00",
    }


def test_property_summary_scoped_paginated_and_read_only(context):
    client, _, org, other = context
    prop = Property.objects.create(organization=org, name="Summary home", address="Private address")
    Property.objects.create(organization=other, name="Other private home", address="Other")
    Unit.objects.create(organization=org, property=prop, name="A", rent_amount=100,
                        occupancy_status="occupied")
    url = f"/api/v1/platform/workspaces/{org.public_id}/properties/"
    response = client.get(url + "?page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["count"] == 1
    assert data["response_data"][0]["occupied_units"] == 1
    assert "Private address" not in response.content.decode()
    assert client.post(url, {}).status_code == 405


@pytest.mark.parametrize("authenticated", [False, True])
def test_dashboard_and_property_summary_require_staff(context, authenticated):
    client, _, org, _ = context
    user = (get_user_model().objects.create_user(username="summary-nonstaff")
            if authenticated else None)
    client.force_authenticate(user)
    for url in [URL, f"/api/v1/platform/workspaces/{org.public_id}/properties/"]:
        assert client.get(url).status_code == 403
