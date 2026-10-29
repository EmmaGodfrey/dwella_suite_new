import csv
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Payment
from apps.billing.services import create_invoice, record_payment, reverse_payment
from apps.billing.tests import make_lease, member_client
from apps.organizations.models import Organization

pytestmark = pytest.mark.django_db


@pytest.fixture
def ledger():
    org = Organization.objects.create(name="Statement portfolio", currency="USD")
    client = member_client(org, "landlord", "report-manager")
    lease = make_lease(org)
    today = timezone.localdate()
    start = today - timedelta(days=10)

    def charge(amount, day):
        return create_invoice(
            organization=org, tenant=lease.tenant, lease=lease,
            issue_date=day, due_date=day,
            lines=[{"kind": "rent", "description": "Rent", "amount": Decimal(amount)}],
        )

    before = charge("100.25", start - timedelta(days=2))
    record_payment(invoice=before, amount=Decimal("40.10"), method="cash",
                   paid_on=start - timedelta(days=1))
    reversed_payment = record_payment(
        invoice=before, amount=Decimal("10"), method="cash", paid_on=start - timedelta(days=1)
    )
    reverse_payment(reversed_payment, reason="Correction", user=client.handler._force_user)
    current = charge("200.35", start)
    second = charge("50.20", start)
    paid = record_payment(invoice=current, amount=Decimal("70.05"), method="bank_transfer",
                          paid_on=start + timedelta(days=1))
    void = charge("33", start)
    void.status, void.voided_at = "void", timezone.now()
    void.save(update_fields=["status", "voided_at"])
    charge("99", today + timedelta(days=1))
    query = {"date_from": str(start), "date_to": str(today)}
    return org, client, lease, query, current, second, paid


def url(report):
    return f"/api/v1/reports/{report}/"


def statement_params(ledger, **extra):
    return {**ledger[3], "tenant": str(ledger[2].tenant.public_id), **extra}


def export_rows(response):
    assert response.status_code == 200
    return list(csv.DictReader(StringIO(b"".join(response.streaming_content).decode("utf-8-sig"))))


def test_collections_use_recorded_valid_payments_and_currency(ledger):
    org, client, _, query, _, _, paid = ledger
    response = client.get(url("collections"), query)
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data["totals"] == {"payments": 1, "amount": "70.05"}
    assert data["by_method"]["bank_transfer"] == "70.05"
    assert data["by_method"]["cash"] == "0.00"
    assert data["rows"][0]["id"] == str(paid.public_id)
    assert data["currency"] == org.currency == "USD"
    assert "not net settlement" in data["basis"]
    assert response["Cache-Control"] == "private, no-store"
    assert response.json()["pagination"]["count"] == 1


def test_collections_filters_and_csv_match(ledger):
    _, client, lease, query, _, _, _ = ledger
    filters = {**query, "tenant": str(lease.tenant.public_id),
               "property": str(lease.unit.property.public_id), "method": "bank_transfer"}
    data = client.get(url("collections"), filters).json()["response_data"]
    rows = export_rows(client.get(url("collections"), {**filters, "export": "csv"}))
    assert len(rows) == data["total_rows"] == 1
    assert Decimal(rows[0]["amount"]) == Decimal(data["totals"]["amount"])
    assert rows[0]["currency"] == "USD"
    assert rows[0]["date_from"] == query["date_from"]
    assert rows[0]["basis"] == data["basis"]
    empty = client.get(url("collections"), {**query, "method": "card"}).json()["response_data"]
    assert empty["rows"] == [] and empty["totals"]["amount"] == "0.00"


def test_statement_exact_opening_closing_and_stable_same_day_order(ledger):
    _, client, _, _, current, second, paid = ledger
    response = client.get(url("tenant-statement"), statement_params(ledger))
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert data["totals"] == {"opening_balance": "60.15", "charges": "250.55",
                              "payments": "70.05", "closing_balance": "240.65"}
    assert [(row["type"], row["id"]) for row in data["rows"]] == [
        ("charge", str(current.public_id)), ("charge", str(second.public_id)),
        ("payment", str(paid.public_id)),
    ]
    assert [row["balance"] for row in data["rows"]] == ["260.50", "310.70", "240.65"]
    assert "not a historical snapshot" in data["basis"]
    assert "national_id" not in str(data) and "reversal_reason" not in str(data)


def test_statement_pages_and_full_export_have_identical_balances(ledger):
    client = ledger[1]
    base = statement_params(ledger)
    pages = [client.get(url("tenant-statement"), {**base, "page_size": 1, "page": page})
             .json()["response_data"] for page in (1, 2, 3)]
    assert [page["page_opening_balance"] for page in pages] == ["60.15", "260.50", "310.70"]
    rows = export_rows(client.get(url("tenant-statement"), {**base, "export": "csv"}))
    assert rows[0]["type"] == "opening_balance" and rows[0]["balance"] == "60.15"
    assert rows[-1]["type"] == "closing_balance" and rows[-1]["balance"] == "240.65"
    assert [row["balance"] for row in rows[1:-1]] == [p["rows"][0]["balance"] for p in pages]
    assert all(row["currency"] == "USD" for row in rows)


def test_statement_empty_period_keeps_opening_and_archived_history(ledger):
    _, client, lease, query, _, _, _ = ledger
    lease.tenant.is_active = False
    lease.tenant.save(update_fields=["is_active"])
    query = statement_params(ledger, date_from=query["date_to"])
    data = client.get(url("tenant-statement"), query).json()["response_data"]
    assert data["rows"] == []
    assert data["tenant"]["archived"]
    assert data["totals"]["opening_balance"] == data["totals"]["closing_balance"] == "240.65"
    rows = export_rows(client.get(url("tenant-statement"), {**query, "export": "csv"}))
    assert len(rows) == 2 and rows[-1]["balance"] == "240.65"


def test_statement_same_day_receipt_prefixes_and_credit_balances(ledger):
    org, client, lease, query, _, _, _ = ledger
    future = lease.invoices.order_by("-issue_date").first()
    start = timezone.localdate() - timedelta(days=10)
    payment = record_payment(invoice=future, amount=Decimal("90"), method="cash",
                             paid_on=start - timedelta(days=1))
    # Payment predates its invoice's issue date: retain the exact credit balance.
    params = statement_params(ledger, date_to=query["date_from"])
    data = client.get(url("tenant-statement"), params).json()["response_data"]
    assert data["totals"]["opening_balance"] == "-29.85"
    rows = export_rows(client.get(url("tenant-statement"), {**params, "export": "csv"}))
    assert Decimal(rows[0]["balance"]) == Decimal("-29.85")
    # Two receipts on the same day must keep their prefix when page two starts
    # at a receipt rather than a charge. Neither the ID nor date may be skipped.
    paid = record_payment(
        invoice=future, amount=Decimal("1"), method="cash", paid_on=payment.paid_on
    )
    params = statement_params(ledger, date_from=str(payment.paid_on))
    complete = client.get(url("tenant-statement"), params).json()["response_data"]["rows"]
    for page in (1, 2):
        part = client.get(url("tenant-statement"), {**params, "page_size": 1, "page": page})
        assert part.json()["response_data"]["rows"][0] == complete[page - 1]
    assert any(row["id"] == str(paid.public_id) for row in complete)


def test_collection_excludes_legacy_payment_on_void_invoice(ledger):
    org, client, lease, query, _, _, _ = ledger
    invoice = lease.invoices.get(status="void")
    Payment.objects.create(organization=org, invoice=invoice, tenant=lease.tenant,
                           receipt_number="RCT-LEGACY", amount=Decimal("5"), method="cash",
                           paid_on=timezone.localdate())
    data = client.get(url("collections"), query).json()["response_data"]
    assert data["totals"]["amount"] == "70.05"


@pytest.mark.parametrize("report", ["collections", "tenant-statement"])
def test_suspended_workspace_cannot_read_or_export_activity(ledger, report):
    org, client, _, query, _, _, _ = ledger
    org.is_active = False
    org.save(update_fields=["is_active"])
    params = statement_params(ledger) if report == "tenant-statement" else query
    for extra in ({}, {"export": "csv"}):
        assert client.get(url(report), {**params, **extra}).status_code == 403


@pytest.mark.parametrize("report", ["collections", "tenant-statement"])
def test_activity_reports_check_fresh_access_and_tenant_scope(ledger, report):
    org, client, lease, query, _, _, _ = ledger
    params = statement_params(ledger) if report == "tenant-statement" else query
    assert APIClient().get(url(report), params).status_code in (401, 403)
    tenant_client = member_client(org, "tenant", "report-tenant")
    assert tenant_client.get(url(report), params).status_code == 403
    other = Organization.objects.create(name="Other report workspace")
    outsider = member_client(other, "landlord", "outsider")
    if report == "tenant-statement":
        assert outsider.get(url(report), params).status_code == 400
    else:
        assert outsider.get(url(report), query).json()["response_data"]["rows"] == []
    assert outsider.get(url(report), {**params, "tenant": str(lease.tenant.public_id)}
                        ).status_code == 400
    assert outsider.get(url(report), {**params, "property": str(lease.unit.property.public_id)}
                        ).status_code == 400
    membership = client.handler._force_user.organization_memberships.get()
    membership.is_active = False
    membership.save(update_fields=["is_active"])
    assert client.get(url(report), params).status_code == 403


@pytest.mark.parametrize("report", ["collections", "tenant-statement"])
@pytest.mark.parametrize("bad", [
    {"date_from": "invalid"}, {"date_from": "2000-01-01"},
    {"date_to": "2099-01-01"}, {"date_from": "2099-01-01"},
    {"tenant": "invalid"}, {"tenant": str(uuid4())}, {"property": "invalid"},
    {"page_size": 101}, {"page": 0}, {"page": 10000}, {"export": "pdf"},
    {"as_of": "2020-01-01"},
])
def test_activity_parameters_are_authoritative(ledger, report, bad):
    query = statement_params(ledger) if report == "tenant-statement" else ledger[3]
    response = ledger[1].get(url(report), {**query, **bad})
    assert response.status_code == 400


def test_statement_requires_tenant_and_valid_method(ledger):
    assert ledger[1].get(url("tenant-statement"), ledger[3]).status_code == 400
    assert ledger[1].get(url("collections"), {**ledger[3], "method": "pending"}).status_code == 400


def test_activity_exports_escape_contact_formulas(ledger):
    _, client, lease, query, _, _, _ = ledger
    lease.tenant.full_name = "=SUM(1,2)"
    lease.tenant.save(update_fields=["full_name"])
    for report, params in [("collections", query), ("tenant-statement", statement_params(ledger))]:
        rows = export_rows(client.get(url(report), {**params, "export": "csv"}))
        assert rows[0]["tenant"].startswith("'=SUM")


@pytest.mark.parametrize("report", ["collections", "tenant-statement"])
def test_activity_query_cost_is_bounded_for_pages_and_consumed_streams(ledger, report):
    org, client, lease, query, current, _, _ = ledger
    params = statement_params(ledger) if report == "tenant-statement" else query

    def cost(**extra):
        with CaptureQueriesContext(connection) as captured:
            response = client.get(url(report), {**params, **extra})
            assert response.status_code == 200
            if response.streaming:
                assert b"".join(response.streaming_content)
            else:
                assert response.json()["success"]
        return len(captured)

    small = cost(page_size=1), cost(export="csv")
    Payment.objects.bulk_create([
        Payment(organization=org, tenant=lease.tenant, invoice=current,
                receipt_number=f"RCT-BUDGET-{number}", amount=Decimal("1"), method="cash",
                paid_on=timezone.localdate()) for number in range(99)
    ])
    full = cost(page_size=100), cost(export="csv")
    assert full == small
    assert cost(page_size=1) == cost(page_size=100)
    if report == "tenant-statement":
        assert cost(page_size=1, page=2) <= small[0] + 2
    print(f"REPORT_ACTIVITY {report}: small={small}, full={full} (JSON, consumed CSV)")


@pytest.mark.parametrize("report", ["collections", "tenant-statement"])
def test_activity_export_throttle_applies_without_blocking_reads(ledger, report, monkeypatch):
    from django.core.cache import cache

    from apps.reports.common import ReportExportThrottle

    client = ledger[1]
    params = statement_params(ledger) if report == "tenant-statement" else ledger[3]
    key = f"throttle_report_export_{client.handler._force_user.pk}"
    cache.delete(key)
    monkeypatch.setattr(ReportExportThrottle, "rate", "1/hour")
    try:
        assert export_rows(client.get(url(report), {**params, "export": "csv"}))
        assert client.get(url(report), {**params, "export": "csv"}).status_code == 429
        assert client.get(url(report), params).status_code == 200
    finally:
        cache.delete(key)
