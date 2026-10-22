from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.services import create_invoice, record_payment, reverse_payment
from apps.billing.tests import make_lease, member_client
from apps.maintenance.models import MaintenanceRequest
from apps.notifications.models import NotificationRead
from apps.organizations.models import Organization

pytestmark = pytest.mark.django_db
URL = "/api/v1/notifications/"


@pytest.fixture
def dataset():
    org = Organization.objects.create(name="Notification portfolio")
    client = member_client(org, "owner", "notification-owner")
    lease = make_lease(org)
    lease.end_date = timezone.localdate() + timedelta(days=20)
    lease.save()
    due = timezone.localdate() - timedelta(days=1)
    invoice = create_invoice(
        organization=org,
        tenant=lease.tenant,
        lease=lease,
        issue_date=due,
        due_date=due,
        lines=[{"kind": "rent", "description": "Rent", "amount": Decimal("100")}],
    )
    repair = MaintenanceRequest.objects.create(
        organization=org, property=lease.unit.property, title="Broken tap", reference="MR-TEST"
    )
    return org, client, lease, invoice, repair


def test_live_alerts_read_state_and_personal_isolation(dataset):
    org, client, _, _, _ = dataset
    data = client.get(URL).json()["response_data"]
    assert data["unread_count"] == 3
    assert {item["kind"] for item in data["items"]} == {"arrears", "lease", "maintenance"}
    ids = [item["id"] for item in data["items"]]
    assert client.post(URL, {"ids": ids}, format="json").status_code == 200
    assert client.post(URL, {"ids": ids}, format="json").status_code == 200
    assert NotificationRead.objects.count() == 3
    assert client.get(URL).json()["response_data"]["unread_count"] == 0
    teammate = member_client(org, "viewer", "notification-viewer")
    assert teammate.get(URL).json()["response_data"]["unread_count"] == 3


def test_resolution_removes_old_alert_and_payment_has_receipt_link(dataset):
    _, client, lease, invoice, repair = dataset
    payment = record_payment(
        invoice=invoice, amount=Decimal("100"), method="cash", paid_on=timezone.localdate()
    )
    repair.status = "completed"
    repair.save()
    lease.status = "ended"
    lease.save()
    data = client.get(URL).json()["response_data"]
    assert [item["kind"] for item in data["items"]] == ["payment"]
    assert data["items"][0]["path"] == f"/billing/receipts/{payment.public_id}"
    reverse_payment(payment, reason="Wrong payment recorded", user=client.handler._force_user)
    data = client.get(URL).json()["response_data"]
    assert [item["kind"] for item in data["items"]] == ["arrears"]


def test_notification_security_and_unknown_ids(dataset):
    org, client, _, _, _ = dataset
    ids = [item["id"] for item in client.get(URL).json()["response_data"]["items"]]
    other = Organization.objects.create(name="Other notifications")
    outsider = member_client(other, "owner", "notification-outsider")
    assert outsider.get(URL).json()["response_data"]["items"] == []
    assert outsider.post(URL, {"ids": ids}, format="json").status_code == 400
    assert not NotificationRead.objects.exists()
    for payload in [{}, {"ids": []}, {"ids": ["arbitrary"]}, {"ids": ["x" * 101]}]:
        assert client.post(URL, payload, format="json").status_code == 400
    tenant = member_client(org, "tenant", "notification-tenant")
    for restricted in [APIClient(), tenant]:
        assert restricted.get(URL).status_code in (401, 403)
        assert restricted.post(URL, {"ids": ids}, format="json").status_code in (401, 403)
    membership = client.handler._force_user.organization_memberships.get()
    membership.is_active = False
    membership.save()
    assert client.get(URL).status_code == 403
