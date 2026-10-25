import hashlib
import io
import json
import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Invoice, Payment
from apps.billing.services import (
    generate_rent_invoices,
)
from apps.billing.tests import THIS_MONTH, make_lease
from apps.organizations.models import Organization, OrganizationMembership

from .evidence import read_exchange, record_exchange
from .models import Collection, Destination, Exchange, Payout
from .provider import Provider, ProviderResult
from .testing import (
    SECRET,
    checkout,
    client_for,
    collection_result,
    http_response,
    paid,
    signature,
    webhook_body,
)
from .worker import run_cycle

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_checkout_is_local_idempotent_and_uses_server_details(home):
    key = uuid.uuid4()
    url = f"/api/v1/payments/tenant/invoices/{home['invoice'].public_id}/checkout/"
    with patch("apps.payments.provider.urllib.request.build_opener") as network:
        client = client_for(home["tenant"])
        response = client.post(
            url, {"amount": "100.00", "idempotency_key": str(key)}, format="json"
        )
        assert response.status_code == 200
        data = response.json()["response_data"]
        assert data["checkout"]["currency"] == "ZMW"
        assert data["checkout"]["amount"] == "100.00"
        assert "secret" not in str(data)
        assert "destination" not in data["collection"]
        assert "payout" not in data["collection"]
        assert (
            client.post(
                url, {"amount": "100.00", "idempotency_key": str(key)}, format="json"
            ).status_code
            == 200
        )
        network.assert_not_called()
    assert Collection.objects.count() == 1


def test_signed_webhook_deduplicates_and_does_not_credit_without_verification(home):
    row = checkout(home)
    body = webhook_body(row)
    client = APIClient()
    with patch("apps.payments.services.Provider") as provider:
        for _ in range(2):
            response = client.post(
                "/api/v1/payments/webhook/",
                body,
                content_type="application/json",
                HTTP_X_LENCO_SIGNATURE=signature(body),
            )
            assert response.status_code == 200
        provider.assert_not_called()
    assert Exchange.objects.filter(operation="webhook").count() == 1
    assert not Payment.objects.exists()
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        run_cycle()
    assert Payment.objects.count() == 1
    row.refresh_from_db()
    assert row.status == "successful" and row.next_check_at is None


@pytest.mark.parametrize(
    "body,sig",
    [(b"{}", ""), (b"{}", "0" * 128), (b"{", "signed"), (b"x" * (128 * 1024 + 1), "")],
    ids=["missing-signature", "wrong-signature", "malformed-json", "oversized"],
)
def test_bad_webhooks_never_create_evidence_or_payments(body, sig):
    if sig == "signed":
        sig = signature(body)
    response = APIClient().post(
        "/api/v1/payments/webhook/",
        body,
        content_type="application/json",
        HTTP_X_LENCO_SIGNATURE=sig,
    )
    assert response.status_code in {400, 403}
    assert not Exchange.objects.exists()


def test_tenant_isolation_manager_scope_and_private_evidence(home):
    row = paid(home)
    other = User.objects.create_user(username="other-tenant", email="other@example.com")
    OrganizationMembership.objects.create(organization=home["org"], user=other, role="tenant")
    other_lease = make_lease(home["org"], unit_name="2B", phone="+260971111112")
    other_lease.tenant.user = other
    other_lease.tenant.save()
    detail = f"/api/v1/payments/tenant/collections/{row.public_id}/"
    assert APIClient().get(detail).status_code in {401, 403}
    assert client_for(other).get(detail).status_code == 404
    assert client_for(home["manager"]).get(detail).status_code == 403
    tenant_response = client_for(home["tenant"]).get(detail)
    assert tenant_response.status_code == 200
    assert tenant_response["Cache-Control"] == "private, no-store"
    for path in ["/api/v1/payments/collections/", "/api/v1/payments/platform/collections/"]:
        assert client_for(home["tenant"]).get(path).status_code == 403
    response = client_for(home["manager"]).get("/api/v1/payments/collections/")
    assert response.status_code == 200
    assert row.reference in response.content.decode()
    assert (
        client_for(home["admin"]).get("/api/v1/payments/platform/collections/").status_code == 200
    )
    evidence = record_exchange(
        environment="sandbox", operation="test", body=b'{"message":"failed"}', collection=row
    )
    path = f"/api/v1/payments/platform/exchanges/{evidence.public_id}/"
    assert client_for(home["manager"]).get(path).status_code == 403
    assert client_for(home["admin"]).get(path).status_code == 200
    listing = client_for(home["admin"]).get(
        f"/api/v1/payments/platform/collections/{row.public_id}/exchanges/"
    )
    assert listing.status_code == 200


def test_cross_workspace_checkout_denied_and_tampered_callback_is_only_a_wakeup(home):
    row = checkout(home)
    other_org = Organization.objects.create(name="Other payments workspace")
    other_lease = make_lease(other_org)
    generate_rent_invoices(other_org, THIS_MONTH)
    invoice = Invoice.objects.get(tenant=other_lease.tenant)
    client = client_for(home["tenant"])
    url = f"/api/v1/payments/tenant/invoices/{invoice.public_id}/checkout/"
    assert (
        client.post(
            url, {"amount": "1", "idempotency_key": str(uuid.uuid4())}, format="json"
        ).status_code
        == 404
    )
    url = f"/api/v1/payments/tenant/collections/{row.public_id}/"
    assert client.post(url, {"status": "successful"}, format="json").status_code == 202
    assert not Payment.objects.exists()


def test_destination_changes_require_platform_admin_and_are_versioned(home):
    path = f"/api/v1/payments/platform/destinations/{home['org'].public_id}/"
    payload = {
        "phone": "0961111111",
        "operator": "mtn",
        "account_name": "Manager",
        "reason": "Confirmed replacement with owner",
    }
    assert client_for(home["manager"]).post(path, payload, format="json").status_code == 403
    admin = client_for(home["admin"])
    assert admin.post(path, {**payload, "phone": "bad"}, format="json").status_code == 400
    assert admin.post(path, payload, format="json").status_code == 201
    home["destination"].refresh_from_db()
    assert not home["destination"].enabled
    assert Destination.objects.filter(organization=home["org"], enabled=True).count() == 1
    home["destination"].phone = "+260971111112"
    with pytest.raises(ValueError, match="new destination"):
        home["destination"].save()


def test_payment_write_throttle(home):
    client = client_for(home["tenant"])
    path = f"/api/v1/payments/tenant/invoices/{home['invoice'].public_id}/checkout/"
    for _ in range(30):
        assert client.post(path, {}, format="json").status_code == 400
    assert client.post(path, {}, format="json").status_code == 429


def test_encrypted_redacted_append_only_evidence(home):
    row = checkout(home)
    body = json.dumps(
        {
            "secret_key": SECRET,
            "cardDetails": {"pan": "4111111111111111", "cvv": "123"},
            "message": f"Bearer {SECRET}",
            "reasonForFailure": "insufficient funds",
        }
    ).encode()
    evidence = record_exchange(
        environment="sandbox",
        operation="collection_status",
        body=body,
        collection=row,
        http_status=400,
    )
    assert SECRET.encode() not in bytes(evidence.encrypted_payload)
    decoded = read_exchange(evidence)
    assert SECRET not in json.dumps(decoded)
    assert "4111111111111111" not in json.dumps(decoded)
    assert decoded["response"]["reasonForFailure"] == "insufficient funds"
    assert evidence.body_sha256 == hashlib.sha256(body).hexdigest()
    with pytest.raises(ValueError):
        evidence.save()
    with pytest.raises(ValueError):
        evidence.delete()


@pytest.mark.parametrize("kind", ["ok", "http", "network", "malformed", "oversized"])
def test_transport_preserves_response_and_failure_evidence(home, kind):
    import urllib.error

    row = checkout(home)
    with patch("apps.payments.provider.urllib.request.build_opener") as build:
        if kind == "network":
            build.return_value.open.side_effect = TimeoutError(SECRET)
        elif kind == "http":
            build.return_value.open.side_effect = urllib.error.HTTPError(
                "https://sandbox.lenco.co",
                400,
                "bad",
                http_response(b"").headers,
                io.BytesIO(b'{"status":false,"message":"insufficient funds"}'),
            )
        else:
            body = (
                b"{"
                if kind == "malformed"
                else b"x" * (1024 * 1024 + 1)
                if kind == "oversized"
                else b'{"status":true,"data":{}}'
            )
            build.return_value.open.return_value = http_response(body)
        result = Provider("sandbox").request("collection_status", collection=row)
        assert build.return_value.open.call_count == 1
        assert build.return_value.open.call_args.args[0].get_method() == "GET"
    evidence = Exchange.objects.get()
    assert evidence.collection_id == row.pk
    assert (result.error != "") == (kind != "ok")
    assert SECRET not in json.dumps(read_exchange(evidence))


def test_environment_isolation(home):
    with pytest.raises(ValueError):
        Provider("live")


def test_payment_tables_are_private_on_postgres(home):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL privileges/RLS")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relname, relrowsecurity FROM pg_class WHERE relname LIKE 'payments_%' "
            "AND relkind='r'"
        )
        rows = cursor.fetchall()
        assert len(rows) == 8 and all(enabled for _, enabled in rows)
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='handy_agent'")
        if cursor.fetchone():
            for table, _ in rows:
                cursor.execute("SELECT has_table_privilege('handy_agent', %s, 'SELECT')", [table])
                assert not cursor.fetchone()[0]


def test_ledger_views_and_notifications_reflect_verified_rent_and_payout_failure(home):
    row = paid(home)
    manager = client_for(home["manager"])
    response = manager.get(f"/api/v1/billing/invoices/{home['invoice'].public_id}/")
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data["amount_paid"] == "100.00"
    assert data["payments"][0]["online_payment"]["reference"] == row.reference
    portal = client_for(home["tenant"]).get("/api/v1/portal/overview/").json()["response_data"]
    assert portal["balance"] == "3800.00"
    Payout.objects.filter(pk=row.payout.pk).update(status="failed")
    alerts = manager.get("/api/v1/notifications/").json()["response_data"]["items"]
    assert any(item["id"].startswith("payout:") for item in alerts)
    assert any(item["id"].startswith("payment:") for item in alerts)


@pytest.mark.parametrize(
    "raw", [b'{"amount":NaN}', b'{"amount":Infinity}', b'{"event":[],"data":{}}']
)
def test_signed_malformed_webhook_types_are_rejected(raw):
    response = APIClient().post(
        "/api/v1/payments/webhook/",
        raw,
        content_type="application/json",
        HTTP_X_LENCO_SIGNATURE=signature(raw),
    )
    assert response.status_code == 400


@pytest.mark.parametrize("raw", [b'{"amount":NaN}', b'{"amount":1e999}'])
def test_nonfinite_response_is_retained_as_safe_evidence(home, raw):
    row = checkout(home)
    with patch("apps.payments.provider.urllib.request.build_opener") as build:
        build.return_value.open.return_value = http_response(raw)
        result = Provider("sandbox").request("collection_status", collection=row)
    assert result.error == "invalid_json"
    assert read_exchange(Exchange.objects.get())["response"]["non_json"]


def test_failed_webhook_requery_remains_queued_for_retry(home):
    row = checkout(home)
    body = webhook_body(row)
    APIClient().post(
        "/api/v1/payments/webhook/",
        body,
        content_type="application/json",
        HTTP_X_LENCO_SIGNATURE=signature(body),
    )
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = ProviderResult({}, 503, "http_error")
        run_cycle()
    row.refresh_from_db()
    assert row.next_check_at > timezone.now() and not Payment.objects.exists()
    Collection.objects.filter(pk=row.pk).update(next_check_at=timezone.now())
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        run_cycle()
    assert Payment.objects.count() == 1


def test_payment_options_follow_enable_switch_and_workspace_approval(home, settings):
    client = client_for(home["tenant"])
    url = "/api/v1/payments/tenant/options/"
    assert client.get(url).json()["response_data"]["enabled"]
    settings.LENCO_PAYMENTS_ENABLED = False
    assert not client.get(url).json()["response_data"]["enabled"]
    settings.LENCO_PAYMENTS_ENABLED = True
    Destination.objects.filter(organization=home["org"]).update(enabled=False)
    assert not client.get(url).json()["response_data"]["enabled"]


def test_history_filters_do_not_cross_invoice_or_workspace(home):
    row = checkout(home)
    client = client_for(home["tenant"])
    response = client.get(
        f"/api/v1/payments/tenant/collections/?invoice={home['invoice'].public_id}"
    )
    assert response.status_code == 200 and row.reference in response.content.decode()
    assert client.get("/api/v1/payments/tenant/collections/?invoice=bad").status_code == 400
    other_org = Organization.objects.create(name="Other manager's payments")
    user = User.objects.create_user(username="unrelated-manager")
    OrganizationMembership.objects.create(organization=other_org, user=user, role="landlord")
    assert (
        row.reference not in client_for(user).get("/api/v1/payments/collections/").content.decode()
    )


def test_webhook_signature_binds_exact_raw_bytes(home):
    row = checkout(home)
    raw = webhook_body(row)
    modified = raw.replace(b'"event":', b'"event" :')
    response = APIClient().post(
        "/api/v1/payments/webhook/",
        modified,
        content_type="application/json",
        HTTP_X_LENCO_SIGNATURE=signature(raw),
    )
    assert response.status_code == 403 and not Exchange.objects.exists()


def test_balance_inspection_is_platform_only_and_money_is_a_string(home):
    from .test_balances import sync_feed

    sync_feed()
    url = "/api/v1/payments/platform/balance/"
    assert client_for(home["tenant"]).get(url).status_code == 403
    assert client_for(home["manager"]).get(url).status_code == 403
    response = client_for(home["admin"]).get(url)
    assert response.status_code == 200
    assert response.json()["response_data"]["ledger_balance"] == "1000.00"


def test_success_webhook_waits_for_authoritative_status_to_catch_up(home, settings):
    settings.LENCO_PAYOUTS_ENABLED = False
    row = checkout(home)
    Collection.objects.filter(pk=row.pk).update(status="failed")
    raw = webhook_body(row)
    assert (
        APIClient()
        .post(
            "/api/v1/payments/webhook/",
            raw,
            content_type="application/json",
            HTTP_X_LENCO_SIGNATURE=signature(raw),
        )
        .status_code
        == 200
    )
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(
            row, state="pending", settled=False
        )
        run_cycle()
    row.refresh_from_db()
    # Still failed locally, but the webhook keeps it under watch.
    assert row.status == "failed" and row.next_check_at and not Payment.objects.exists()
    Collection.objects.filter(pk=row.pk).update(next_check_at=timezone.now())
    with patch("apps.payments.services.Provider") as provider:
        provider.return_value.request.return_value = collection_result(row)
        run_cycle()
    assert Payment.objects.count() == 1


def test_repeating_the_same_destination_approval_keeps_one_version(home):
    from .services import approve_destination

    again = approve_destination(
        organization=home["org"],
        user=home["admin"],
        phone="+260971111111",
        operator="airtel",
        account_name="Manager Wallet",
        reason="Same request sent twice by a double click",
    )
    assert again.pk == home["destination"].pk
    assert Destination.objects.filter(organization=home["org"]).count() == 1


def test_an_open_payment_blocks_a_second_one_and_says_until_when(home):
    checkout(home)
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError, match="still open until"):
        checkout(home, amount="60.00")
