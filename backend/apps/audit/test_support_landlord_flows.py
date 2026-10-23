from datetime import timedelta

import pytest
from django.utils import timezone

from apps.billing.models import Invoice, Payment
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import AuditEvent
from .support_test_utils import start

pytestmark = pytest.mark.django_db


def test_acting_owner_completes_lease_billing_and_maintenance_lifecycle(context):
    client, admin, org, other = context
    session = start(client, org)
    prop = Property.objects.create(organization=org, name="Support lifecycle", address="Plot 1")
    unit = Unit.objects.create(organization=org, property=prop, name="A", rent_amount=1000)
    tenant = Tenant.objects.create(
        organization=org, full_name="Synthetic tenant", phone_number="000",
    )
    today = timezone.localdate()

    def post(path, payload, expected=200):
        response = client.post("/api/v1/" + path, payload, format="json")
        assert response.status_code == expected, response.content
        return response.json()["response_data"]

    lease = post("leases/", {
        "tenant": str(tenant.public_id), "unit": str(unit.public_id),
        "start_date": str(today - timedelta(days=30)),
        "end_date": str(today + timedelta(days=330)),
    }, 201)
    post(f"leases/{lease['id']}/activate/", {})
    post("billing/invoices/generate/", {"period": f"{today:%Y-%m}"})
    invoice = Invoice.objects.get(organization=org)
    path = f"billing/invoices/{invoice.public_id}/"
    post(path + "record-payment/", {"amount": "100", "method": "cash"}, 201)
    payment = Payment.objects.get(organization=org)
    receipt = client.get(f"/api/v1/billing/payments/{payment.public_id}/")
    assert receipt.status_code == 200
    post(f"billing/payments/{payment.public_id}/reverse/", {"reason": "Wrong amount recorded"})
    post(path + "void/", {})
    post(f"leases/{lease['id']}/end/", {})
    repair = post("maintenance/requests/", {
        "title": "Support repair", "description": "Tap dripping", "category": "plumbing",
        "property": str(prop.public_id), "unit": str(unit.public_id), "priority": "normal",
    }, 201)
    post(f"maintenance/requests/{repair['id']}/start/", {})
    post(f"maintenance/requests/{repair['id']}/complete/", {"resolution": "Tap fixed"})
    for path in ["reports/rent-roll/?export=csv", "reports/arrears/?export=csv", "notifications/"]:
        assert client.get("/api/v1/" + path).status_code == 200
    events = AuditEvent.objects.filter(action__startswith="support.")
    assert events.count() >= 9
    assert all(e.actor == admin and e.organization == org
               and e.metadata["support_session"] == str(session.public_id) for e in events)
    assert not Invoice.objects.filter(organization=other).exists()

    session.expires_at = timezone.now() - timedelta(seconds=1)
    session.save(update_fields=["expires_at"])
    assert client.get("/api/v1/billing/invoices/").status_code == 403
    assert client.post("/api/v1/leases/", {}, format="json").status_code == 403
