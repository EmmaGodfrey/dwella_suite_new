from unittest.mock import patch

import pytest
from django.core import mail
from django.test import override_settings

from apps.audit.models import AuditEvent
from apps.marketing.emails import due_steps
from apps.marketing.models import BetaApplication, BetaEmail

from .models import Contact, Enrollment, Suppression
from .tests import BASE, contact

pytestmark = pytest.mark.django_db


@override_settings(
    BETA_EMAILS_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
def test_early_access_links_signup_delivers_once_and_stops_countdown(staff):
    client, _ = staff
    person = contact(client)
    path = BASE + f"contacts/{person['id']}/early-access/"
    for _ in range(2):
        response = client.post(path, {}, format="json")
        assert response.status_code == 200, response.content
    application = BetaApplication.objects.get()
    assert application.account_id
    assert Contact.objects.get().beta_application == application
    assert BetaEmail.objects.filter(kind="access").count() == 1
    assert len(mail.outbox) == 1
    assert due_steps(application) == []
    assert Enrollment.objects.filter(sequence__name="Early tester check-ins").count() == 1


@pytest.mark.parametrize("blocked", ["suppressed", "no_email", "no_smtp"])
def test_early_access_refuses_blocked_contacts_without_accounts_or_emails(staff, blocked):
    client, _ = staff
    person = contact(client, email="" if blocked == "no_email" else "example@example.com")
    if blocked == "suppressed":
        Suppression.objects.create(email="example@example.com", reason="manual")
    response = client.post(BASE + f"contacts/{person['id']}/early-access/", {}, format="json")
    assert response.status_code == 400
    assert not BetaEmail.objects.exists()
    assert not BetaApplication.objects.exists()


@override_settings(
    BETA_EMAILS_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
def test_audit_failure_prevents_access_delivery(staff):
    client, _ = staff
    person = contact(client)
    with patch("apps.outreach.early_access.record_event", side_effect=RuntimeError("audit")):
        with pytest.raises(RuntimeError):
            client.post(BASE + f"contacts/{person['id']}/early-access/", {}, format="json")
    assert not BetaApplication.objects.exists()
    assert not mail.outbox


@override_settings(
    BETA_EMAILS_ENABLED=True, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
def test_add_signup_with_access_skips_welcome_and_has_early_filter(staff):
    client, _ = staff
    response = client.post(
        "/api/v1/marketing/admin/beta-applications/",
        {
            "name": "Synthetic tester",
            "email": "early@example.com",
            "phone": "+260971000000",
            "role": "Landlord",
            "units": "1–5",
            "give_early_access": True,
            "send_welcome": True,
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    assert response.json()["response_data"]["early_access"] is True
    assert list(BetaEmail.objects.values_list("kind", flat=True)) == ["access"]
    assert (
        len(
            client.get("/api/v1/marketing/admin/beta-applications/?early_access=true").json()[
                "response_data"
            ]
        )
        == 1
    )
    assert AuditEvent.objects.filter(action="marketing.beta_early_access").exists()
