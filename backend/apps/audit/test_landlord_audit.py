from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Invoice
from apps.billing.tests import make_lease
from apps.organizations.models import OrganizationMembership

from .models import AuditEvent

pytestmark = pytest.mark.django_db


def test_landlord_financial_write_and_audit_fail_together(context):
    client, actor, org, _ = context
    actor.is_staff = False
    actor.save()
    OrganizationMembership.objects.create(user=actor, organization=org, role="landlord")
    lease = make_lease(org)
    invoice = Invoice.objects.create(
        organization=org,
        tenant=lease.tenant,
        lease=lease,
        reference="INV-AUDIT",
        total=100,
        status="open",
        issue_date=timezone.localdate(),
        due_date=timezone.localdate(),
    )
    path = f"/api/v1/billing/invoices/{invoice.public_id}/void/"
    with patch("apps.audit.middleware.record_event", side_effect=RuntimeError("Audit unavailable")):
        with pytest.raises(RuntimeError, match="Audit unavailable"):
            client.post(path, {}, format="json")
    invoice.refresh_from_db()
    assert invoice.status == "open"
    assert client.post(path, {}, format="json").status_code == 200
    event = AuditEvent.objects.get(action="invoice.voided")
    assert event.actor == actor and event.organization == org
    assert event.resource_id == str(invoice.public_id)
    assert client.post(path, {}, format="json").status_code == 400
    assert AuditEvent.objects.filter(action="invoice.voided").count() == 1


def test_successful_login_and_2fa_changes_are_audited_without_secrets():
    user = get_user_model().objects.create_user(
        username="audit@example.com", email="audit@example.com", password="PreviewOnly27!Dwella"
    )
    client = APIClient()
    assert (
        client.post(
            "/api/v1/accounts/login/",
            {
                "email": user.email,
                "password": "wrong",
            },
            format="json",
        ).status_code
        == 400
    )
    assert not AuditEvent.objects.exists()
    response = client.post(
        "/api/v1/accounts/login/",
        {
            "email": user.email,
            "password": "PreviewOnly27!Dwella",
        },
        format="json",
    )
    assert response.status_code == 200
    assert AuditEvent.objects.get(action="account.signed_in").actor == user
    client.force_authenticate(user)
    setup = client.post("/api/v1/accounts/2fa/setup/", {}, format="json")
    assert setup.status_code == 200
    import time

    from apps.accounts.models import TwoFactorDevice
    from apps.accounts.security import _hotp

    TwoFactorDevice.objects.filter(user=user).update(is_confirmed=True)
    code = _hotp(setup.data["secret"], int(time.time() // 30))
    assert (
        client.post(
            "/api/v1/accounts/2fa/disable/",
            {"password": "PreviewOnly27!Dwella", "code": code},
            format="json",
        ).status_code
        == 200
    )
    assert set(AuditEvent.objects.values_list("action", flat=True)) == {
        "account.signed_in",
        "account.2fa_setup_started",
        "account.2fa_disabled",
    }
    assert all(event.metadata == {} for event in AuditEvent.objects.all())
