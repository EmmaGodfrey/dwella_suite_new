from datetime import date
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.accounts.access_state import require_new_account_verification
from apps.audit.models import AuditEvent
from apps.billing.models import Invoice, PaymentInstruction
from apps.billing.tests import member_client
from apps.leases.models import Lease
from apps.notifications.models import MessageDelivery, ReminderPreferences
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

from .models import Organization, OrganizationMembership
from .onboarding import SetupWriteThrottle, setup_status
from .test_onboarding import URL, unassigned_client

pytestmark = pytest.mark.django_db
BUSINESS = {
    "stage": "business", "business_name": "Garden Rentals", "email": "rent@example.com",
    "phone_number": "+260971234567", "address": "Plot 1", "town": "Lusaka",
    "country": "Zambia", "confirm_region": True,
}
BILLING = {
    "stage": "billing", "auto_invoice": False, "invoice_lead_days": 5,
    "reminders": {"email_enabled": False, "whatsapp_enabled": False,
                  "before_due_days": 3, "due_hour": 9, "overdue_every_days": 3,
                  "overdue_repeats": 2},
}


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def post(client, body, code=200):
    response = client.post(URL, body, format="json")
    assert response.status_code == code, response.content
    return response.json()["response_data"]


def finish_account(client, methods=None):
    post(client, BUSINESS)
    post(client, {"stage": "payments", "payment_methods": methods or ["cash"]})
    post(client, BILLING)
    return post(client, {"stage": "complete"})


def portfolio(org):
    prop = Property.objects.create(
        organization=org, name="Home", property_type="house", address="Plot 1",
    )
    unit = Unit.objects.create(organization=org, property=prop, name="Main", rent_amount=1000)
    tenant = Tenant.objects.create(
        organization=org, full_name="Test Tenant", phone_number="+260971234500", status="active",
    )
    lease = Lease.objects.create(
        organization=org, tenant=tenant, unit=unit, reference="LSE-0001", status="active",
        start_date=date(2026, 1, 1), end_date=date(2027, 1, 1), monthly_rent=1000,
    )
    invoice = Invoice.objects.create(
        organization=org, lease=lease, unit=unit, tenant=tenant, reference="INV-0001",
        issue_date=date(2026, 11, 1), due_date=date(2026, 11, 5),
    )
    return prop, unit, tenant, lease, invoice


def test_account_only_cash_setup_persists_without_portfolio_or_messages():
    user, client = unassigned_client()
    assert not client.get(URL).json()["response_data"]["account_ready"]
    assert not Organization.objects.exists()  # GET never writes defaults.
    data = finish_account(client)
    org = OrganizationMembership.objects.get(user=user).organization
    assert data["account_ready"]
    assert not data["complete"]
    assert data["payment_methods"] == ["cash"]
    assert all(step["done"] for step in data["account_steps"])
    assert not any(model.objects.exists() for model in (Property, Unit, Tenant, Lease, Invoice))
    assert not PaymentInstruction.objects.exists()
    assert not MessageDelivery.objects.exists()
    assert org.address == BUSINESS["address"]
    assert org.auto_invoice is False
    assert ReminderPreferences.objects.get(organization=org).overdue_repeats == 2
    assert AuditEvent.objects.filter(action__startswith="organizations.setup_").count() == 4
    assert client.get(URL).json()["response_data"]["account_ready"]


@pytest.mark.parametrize("field,value", [
    ("business_name", " "), ("email", "bad"), ("phone_number", "abc"),
    ("address", ""), ("town", ""), ("country", ""), ("confirm_region", False),
    ("address", "x" * 2001),
])
def test_business_validation_is_atomic(field, value):
    _, client = unassigned_client()
    post(client, {**BUSINESS, field: value}, 400)
    assert not Organization.objects.exists()
    assert not OrganizationMembership.objects.exists()


@pytest.mark.parametrize("stage", ["business", "payments", "billing", "complete"])
@pytest.mark.parametrize("role", ["tenant", "manager"])
def test_non_admin_cannot_change_account_setup(role, stage):
    org = Organization.objects.create(name="Protected")
    client = member_client(org, role, "non-admin")
    post(client, {**BUSINESS, "stage": stage}, 403)
    org.refresh_from_db()
    assert org.display_name == ""
    assert not org.setup_confirmed
    if role == "manager":
        data = client.get(URL).json()["response_data"]
        assert not data["can_setup"]
        assert data["account_steps"] == []


def test_unauthenticated_unverified_and_suspended_access_remain_blocked():
    post(APIClient(), BUSINESS, 403)
    user, client = unassigned_client()
    require_new_account_verification(user)
    post(client, BUSINESS, 403)
    assert client.get(URL).status_code == 403
    org = Organization.objects.create(name="Suspended", is_active=False)
    client = member_client(org, "landlord", "suspended")
    post(client, BUSINESS, 403)


@pytest.mark.parametrize("extra", [
    {"organization": "foreign"}, {"setup_confirmed": True}, {"role": "landlord"},
    {"currency": "USD"}, {"timezone": "UTC"},
])
def test_no_client_workspace_or_readiness_override(extra):
    other = Organization.objects.create(name="Foreign")
    _, client = unassigned_client()
    post(client, {**BUSINESS, **extra}, 400)
    assert Organization.objects.count() == 1
    other.refresh_from_db()
    assert not other.display_name


@pytest.mark.parametrize("stage", [None, [], {}, "unknown"])
def test_malformed_stage_is_a_validation_error(stage):
    _, client = unassigned_client()
    post(client, {"stage": stage}, 400)
    assert not Organization.objects.exists()


@pytest.mark.parametrize("body", [[], "stage", 12, None])
def test_malformed_body_is_a_validation_error(body):
    _, client = unassigned_client()
    post(client, body, 400)
    assert not Organization.objects.exists()


def test_owner_updates_existing_portfolio_without_duplicates_and_completion_is_fresh():
    org = Organization.objects.create(name="Existing")
    prop, _, _, _, invoice = portfolio(org)
    client = member_client(org, "landlord", "owner")
    assert not client.get(URL).json()["response_data"]["complete"]
    assert finish_account(client)["complete"]
    assert Organization.objects.count() == Property.objects.count() == Unit.objects.count() == 1
    assert Invoice.objects.count() == 1
    org.refresh_from_db()
    org.address = ""
    org.save(update_fields=["address"])
    assert not client.get(URL).json()["response_data"]["account_ready"]
    post(client, {"stage": "complete"}, 400)
    post(client, BUSINESS)
    assert post(client, {"stage": "complete"})["complete"]
    invoice.status = "void"
    invoice.save(update_fields=["status"])
    data = client.get(URL).json()["response_data"]
    assert not data["complete"]
    assert not next(item for item in data["steps"] if item["key"] == "invoice")["done"]
    prop.management_status = "archived"
    prop.save(update_fields=["management_status"])
    data = client.get(URL).json()["response_data"]
    assert not next(item for item in data["steps"] if item["key"] == "property")["done"]
    assert not next(item for item in data["steps"] if item["key"] == "lease")["done"]


@pytest.mark.parametrize("methods", [[], ["fake"], ["cash", "cash"], ["bank"], ["mobile_money"]])
def test_payment_method_choice_requires_valid_saved_details(methods):
    _, client = unassigned_client()
    post(client, BUSINESS)
    post(client, {"stage": "payments", "payment_methods": methods}, 400)
    assert not Organization.objects.get().setup_payment_methods


def test_mixed_methods_use_existing_instructions_and_deleted_details_reopen_setup():
    _, client = unassigned_client()
    post(client, BUSINESS)
    org = Organization.objects.get()
    bank = PaymentInstruction.objects.create(
        organization=org, kind="bank", account_name="Owner", bank_name="Bank",
        account_number="1234567",
    )
    mobile = PaymentInstruction.objects.create(
        organization=org, kind="mobile_money", account_name="Owner", network="airtel",
        phone="+260971234567",
    )
    post(client, {"stage": "payments", "payment_methods": ["cash"]}, 400)
    assert finish_account(client, ["bank", "mobile_money", "cash"])["account_ready"]
    bank.delete()
    assert not client.get(URL).json()["response_data"]["account_ready"]
    assert mobile.network == "airtel"


def test_other_workspace_instruction_cannot_satisfy_selected_method():
    other = Organization.objects.create(name="Foreign")
    PaymentInstruction.objects.create(
        organization=other, kind="bank", account_name="Foreign", bank_name="Bank",
        account_number="1234567",
    )
    _, client = unassigned_client()
    post(client, BUSINESS)
    post(client, {"stage": "payments", "payment_methods": ["bank"]}, 400)


@pytest.mark.parametrize("body", [
    {"stage": "complete"},
    {**BILLING, "invoice_lead_days": 29},
    {**BILLING, "reminders": {"due_hour": 24}},
    {**BILLING, "reminders": {"overdue_repeats": 4}},
    {**BILLING, "reminders": {"run_date": "2026-11-16"}},
])
def test_review_and_billing_validation_do_not_mutate_settings(body):
    _, client = unassigned_client()
    post(client, BUSINESS)
    post(client, body, 400)
    assert not ReminderPreferences.objects.exists()
    assert not Organization.objects.get().setup_billing_reviewed


def test_repeat_business_save_reuses_workspace_and_audit_failure_rolls_back():
    _, client = unassigned_client()
    post(client, BUSINESS)
    post(client, BUSINESS)
    assert Organization.objects.count() == OrganizationMembership.objects.count() == 1
    with patch("apps.organizations.setup_account.record_event", side_effect=RuntimeError("audit")):
        with pytest.raises(RuntimeError):
            post(client, {**BUSINESS, "business_name": "Must roll back"})
    assert Organization.objects.get().display_name == BUSINESS["business_name"]


def test_setup_write_throttle_and_safe_reads():
    _, client = unassigned_client()
    with patch.object(SetupWriteThrottle, "rate", "1/hour"):
        post(client, BUSINESS)
        post(client, BUSINESS, 429)
        assert client.get(URL).status_code == 200


def test_readiness_query_count_does_not_grow_with_portfolio_size():
    user, client = unassigned_client()
    finish_account(client)
    org = Organization.objects.get()
    portfolio(org)
    with CaptureQueriesContext(connection) as small:
        setup_status(user)
    Property.objects.bulk_create([
        Property(organization=org, name=f"Home {index}", property_type="house", address="Plot")
        for index in range(30)
    ])
    with CaptureQueriesContext(connection) as full:
        setup_status(user)
    assert len(full) == len(small)
    assert len(full) <= 8
    print(f"Setup readiness: {len(small)} queries for 1 property; {len(full)} for 31")
