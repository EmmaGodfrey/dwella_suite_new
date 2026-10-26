import hashlib
import hmac
import json
import uuid
from email.message import Message
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Invoice
from apps.billing.services import (
    generate_rent_invoices,
)
from apps.billing.tests import THIS_MONTH, make_lease
from apps.organizations.models import Organization, OrganizationMembership

from .models import BalanceSnapshot, ProviderAccount
from .provider import ProviderResult
from .services import approve_destination, reconcile_collection, start_checkout

pytestmark = pytest.mark.django_db
User = get_user_model()
ACCOUNT = "00000000-0000-0000-0000-000000000001"
SECRET = "lenco-fake-test-secret-not-real"


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture(autouse=True)
def configuration(settings):
    settings.LENCO_ENVIRONMENT = "sandbox"
    settings.LENCO_PUBLIC_KEY = "lenco-fake-public-key"
    settings.LENCO_SECRET_KEY = SECRET
    settings.LENCO_PAYMENTS_ENABLED = True
    settings.LENCO_PAYOUTS_ENABLED = True
    # Legacy per-collection payout tests; withdrawal tests switch this off.
    settings.LENCO_AUTOMATIC_PAYOUTS = True
    settings.LENCO_DEBIT_ACCOUNT_ID = ACCOUNT
    cache.clear()


@pytest.fixture
def home():
    org = Organization.objects.create(name="Payments workspace")
    lease = make_lease(org)
    generate_rent_invoices(org, THIS_MONTH)
    invoice = Invoice.objects.get(tenant=lease.tenant)
    tenant = User.objects.create_user(username="rent-tenant", email="tenant@example.com")
    manager = User.objects.create_user(username="rent-manager", email="manager@example.com")
    admin = User.objects.create_user(username="rent-admin", is_superuser=True)
    for user, role in [(tenant, "tenant"), (manager, "landlord")]:
        OrganizationMembership.objects.create(organization=org, user=user, role=role)
    lease.tenant.user = tenant
    lease.tenant.save()
    destination = approve_destination(
        organization=org,
        user=admin,
        phone="+260971111111",
        operator="airtel",
        account_name="Manager Wallet",
        reason="Confirmed with the workspace owner",
    )
    account = ProviderAccount.objects.create(
        environment="sandbox",
        account_id=ACCOUNT,
        currency="ZMW",
        opening_balance=100000,
        checked_at=timezone.now(),
    )
    BalanceSnapshot.objects.create(
        account=account,
        available_balance=100000,
        ledger_balance=100000,
        expected_balance=100000,
        difference=0,
        held_for_landlords=0,
        surplus=100000,
        status="matched",
    )
    return {
        "org": org,
        "invoice": invoice,
        "tenant": tenant,
        "manager": manager,
        "admin": admin,
        "destination": destination,
    }


def checkout(home, amount="100.00", key=None):
    return start_checkout(
        invoice=home["invoice"],
        user=home["tenant"],
        amount=amount,
        idempotency_key=key or uuid.uuid4(),
    )


def collection_result(row, *, state="successful", settled=True, **overrides):
    data = {
        "id": "provider-collection-1",
        "reference": row.reference,
        "amount": str(row.amount),
        "currency": "ZMW",
        "status": state,
        "type": "mobile-money",
        "fee": "2.50",
        "settlementStatus": "settled" if settled else "pending",
        "settlement": {
            "status": "settled",
            "accountId": ACCOUNT,
            "currency": "ZMW",
            "amountSettled": "97.50",
        },
    }
    data.update(overrides)
    return ProviderResult({"status": True, "data": data}, 200)


def payout_result(row, state="successful", **overrides):
    data = {
        "id": "provider-payout-1",
        "reference": row.reference,
        "amount": str(row.amount),
        "currency": "ZMW",
        "accountId": ACCOUNT,
        "status": state,
        "fee": "1.00",
        "creditAccount": {"type": "mobile-money", "phone": "0971111111", "operator": "airtel"},
    }
    data.update(overrides)
    return ProviderResult({"status": True, "data": data}, 200)


def paid(home, settled=True):
    row = checkout(home)
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row, settled=settled)
        reconcile_collection(row)
    row.refresh_from_db()
    return row


def signature(body):
    return hmac.new(
        hashlib.sha256(SECRET.encode()).hexdigest().encode(), body, hashlib.sha512
    ).hexdigest()


def webhook_body(row, **kwargs):
    return json.dumps(
        {"event": "collection.successful", "data": {"reference": row.reference}, **kwargs}
    ).encode()


def http_response(body, status=200, content_type="application/json"):
    result = Mock()
    result.status = status
    result.headers = Message()
    result.headers["Content-Type"] = content_type
    result.read.return_value = body
    result.__enter__ = Mock(return_value=result)
    result.__exit__ = Mock(return_value=False)
    return result
