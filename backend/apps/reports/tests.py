import csv
from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Invoice
from apps.billing.services import create_invoice, record_payment
from apps.billing.tests import make_lease, member_client
from apps.organizations.models import Organization
from apps.properties.models import Unit

pytestmark = pytest.mark.django_db


def body(response):
    return b"".join(response.streaming_content).decode("utf-8-sig")


@pytest.fixture
def dataset():
    org = Organization.objects.create(name="Reports portfolio")
    client = member_client(org, "landlord", "report-owner")
    lease = make_lease(org)
    today = timezone.localdate()
    invoices = []
    for age in [0, 1, 30, 31, 60, 61, 90, 91]:
        due = today - timedelta(days=age)
        invoices.append(
            create_invoice(
                organization=org,
                tenant=lease.tenant,
                lease=lease,
                issue_date=due,
                due_date=due,
                lines=[{"kind": "rent", "description": "Rent", "amount": Decimal("100")}],
            )
        )
    record_payment(invoice=invoices[1], amount=Decimal("25"), method="cash", paid_on=today)
    return org, client, lease, invoices


def test_aging_bands_and_totals_exclude_due_today(dataset):
    _, client, _, invoices = dataset
    data = client.get("/api/v1/reports/arrears/").json()["response_data"]
    assert data["total_rows"] == 7
    assert data["totals"] == {
        "balance": "675.00",
        "days_1_30": "175.00",
        "days_31_60": "200.00",
        "days_61_90": "200.00",
        "days_91_plus": "100.00",
        "invoices": 7,
    }
    assert str(invoices[0].public_id) not in [row["invoice_id"] for row in data["rows"]]
    assert data["rows"][0]["days_overdue"] == 91


def test_rent_roll_active_leases_vacancies_and_unit_balances(dataset):
    org, client, lease, _ = dataset
    Unit.objects.create(
        organization=org, property=lease.unit.property, name="Empty flat", rent_amount=4500
    )
    data = client.get("/api/v1/reports/rent-roll/").json()["response_data"]
    assert data["totals"] == {
        "units": 2,
        "occupied": 1,
        "monthly_rent": "3900.00",
        "balance": "775.00",
    }
    rented = next(row for row in data["rows"] if row["lease_id"])
    assert rented["tenant"] == lease.tenant.full_name
    assert rented["balance"] == "775.00"
    empty = next(row for row in data["rows"] if not row["lease_id"])
    assert empty["monthly_rent"] == "0.00"


@pytest.mark.parametrize("report", ["rent-roll", "arrears"])
def test_property_filter_pagination_and_full_export(dataset, report):
    _, client, lease, _ = dataset
    base = f"/api/v1/reports/{report}/?property={lease.unit.property.public_id}"
    data = client.get(base + "&page_size=1").json()["response_data"]
    assert len(data["rows"]) == 1
    exported = client.get(base + "&page_size=1&export=csv")
    assert exported.status_code == 200
    assert exported["Content-Type"].startswith("text/csv")
    csv_rows = list(csv.reader(StringIO(body(exported))))
    assert len(csv_rows) == data["total_rows"] + 1
    assert "attachment;" in exported["Content-Disposition"]


def test_exports_escape_spreadsheet_formulas(dataset):
    _, client, lease, _ = dataset
    lease.tenant.full_name = '=HYPERLINK("https://example.com")'
    lease.tenant.save()
    response = client.get("/api/v1/reports/arrears/?export=csv")
    rows = list(csv.DictReader(StringIO(body(response))))
    assert rows[0]["tenant"].startswith("'=HYPERLINK")


@pytest.mark.parametrize("report", ["rent-roll", "arrears"])
def test_reports_do_not_leak_portfolios_or_allow_tenants(dataset, report):
    org, client, lease, _ = dataset
    url = f"/api/v1/reports/{report}/"
    assert APIClient().get(url).status_code in (401, 403)
    tenant = member_client(org, "tenant", "report-tenant")
    assert tenant.get(url).status_code == 403
    other = Organization.objects.create(name="Other report portfolio")
    other_client = member_client(other, "landlord", "report-outsider")
    assert other_client.get(url).json()["response_data"]["rows"] == []
    assert other_client.get(url + f"?property={lease.unit.property.public_id}").status_code == 400
    membership = client.handler._force_user.organization_memberships.get()
    membership.is_active = False
    membership.save()
    assert client.get(url).status_code == 403


@pytest.mark.parametrize(
    "query", ["property=bad", "page=0", "page=10000", "page_size=101", "export=pdf"]
)
def test_report_parameters_validate(dataset, query):
    _, client, _, _ = dataset
    assert client.get("/api/v1/reports/arrears/?" + query).status_code == 400


def test_voided_and_paid_invoices_are_not_arrears(dataset):
    _, client, _, invoices = dataset
    Invoice.objects.filter(pk=invoices[-1].pk).update(status="void")
    record_payment(
        invoice=invoices[-2], amount=Decimal("100"), method="cash", paid_on=timezone.localdate()
    )
    data = client.get("/api/v1/reports/arrears/").json()["response_data"]
    assert data["total_rows"] == 5
    assert data["totals"]["balance"] == "475.00"


@pytest.mark.parametrize("report", ["rent-roll", "arrears"])
def test_report_queries_do_not_grow_with_the_portfolio(dataset, report):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    org, client, lease, _ = dataset
    url = f"/api/v1/reports/{report}/"

    def queries(path):
        with CaptureQueriesContext(connection) as captured:
            response = client.get(path)
            assert response.status_code == 200
            if response.streaming:
                # Streaming queries execute while iterating, after get() returns.
                assert b"".join(response.streaming_content)
        return len(captured)

    before = queries(url), queries(url + "?export=csv")
    for n in range(20):
        unit = Unit.objects.create(
            organization=org, property=lease.unit.property, name=f"Flat {n}", rent_amount=100
        )
        create_invoice(
            organization=org, tenant=lease.tenant, unit=unit,
            issue_date=timezone.localdate() - timedelta(days=40),
            due_date=timezone.localdate() - timedelta(days=40),
            lines=[{"kind": "rent", "description": "Rent", "amount": Decimal("10")}],
        )
    after = queries(url), queries(url + "?export=csv")
    print(f"REPORT_BASELINE {report}: small={before}, full={after} (JSON, consumed CSV)")
    assert after == before
    assert queries(url + "?page_size=1") == queries(url + "?page_size=100")


def test_report_pagination_and_private_headers(dataset):
    _, client, _, _ = dataset
    response = client.get("/api/v1/reports/arrears/?page_size=1")
    payload = response.json()
    assert response["Cache-Control"] == "private, no-store"
    assert payload["pagination"]["count"] == payload["response_data"]["total_rows"] == 7
    assert payload["pagination"]["page_size"] == 1
    assert "page=2" in payload["pagination"]["next"]
    assert payload["pagination"]["previous"] is None
    exported = client.get("/api/v1/reports/arrears/?export=csv")
    assert exported["Cache-Control"] == "private, no-store"
    assert body(exported)


def test_report_does_not_silently_ignore_historical_filter(dataset):
    _, client, _, _ = dataset
    response = client.get("/api/v1/reports/arrears/?as_of=2020-01-01")
    assert response.status_code == 400
    assert "as_of" in response.json()["response_data"]


def test_report_uses_the_workspaces_date(dataset, monkeypatch):
    from datetime import UTC, datetime

    from apps.reports import common

    org, client, _, _ = dataset
    org.timezone = "Pacific/Kiritimati"
    org.save(update_fields=["timezone"])
    monkeypatch.setattr(common.timezone, "now", lambda: datetime(2026, 10, 28, 13, tzinfo=UTC))
    assert client.get("/api/v1/reports/arrears/").json()["response_data"]["as_of"] == "2026-10-29"


def test_report_export_throttle_does_not_block_json(dataset, monkeypatch):
    from django.core.cache import cache

    from apps.reports.common import ReportExportThrottle

    _, client, _, _ = dataset
    key = f"throttle_report_export_{client.handler._force_user.pk}"
    cache.delete(key)
    monkeypatch.setattr(ReportExportThrottle, "rate", "1/hour")
    try:
        assert body(client.get("/api/v1/reports/arrears/?export=csv"))
        assert client.get("/api/v1/reports/rent-roll/?export=csv").status_code == 429
        assert client.get("/api/v1/reports/rent-roll/").status_code == 200
    finally:
        cache.delete(key)


@pytest.mark.parametrize("report", ["rent-roll", "arrears"])
def test_current_report_exports_retain_currency_date_and_balance_basis(dataset, report):
    org, client, _, _ = dataset
    org.currency = "USD"
    org.save(update_fields=["currency"])
    path = f"/api/v1/reports/{report}/"
    data = client.get(path).json()["response_data"]
    rows = list(csv.DictReader(StringIO(body(client.get(path, {"export": "csv"})))))
    assert rows and all(row["currency"] == "USD" for row in rows)
    assert all(row["as_of"] == data["as_of"] for row in rows)
    assert all(row["basis"] == data["basis"] for row in rows)
    if report == "rent-roll":
        assert "previous tenants" in data["basis"]
    else:
        assert "not a historical snapshot" in data["basis"]
