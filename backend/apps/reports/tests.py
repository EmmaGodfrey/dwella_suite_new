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


@pytest.fixture
def dataset():
    org = Organization.objects.create(name="Reports portfolio")
    client = member_client(org, "owner", "report-owner")
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
    csv_rows = list(csv.reader(StringIO(exported.content.decode("utf-8-sig"))))
    assert len(csv_rows) == data["total_rows"] + 1
    assert "attachment;" in exported["Content-Disposition"]


def test_exports_escape_spreadsheet_formulas(dataset):
    _, client, lease, _ = dataset
    lease.tenant.full_name = '=HYPERLINK("https://example.com")'
    lease.tenant.save()
    response = client.get("/api/v1/reports/arrears/?export=csv")
    rows = list(csv.DictReader(StringIO(response.content.decode("utf-8-sig"))))
    assert rows[0]["tenant"].startswith("'=HYPERLINK")


@pytest.mark.parametrize("report", ["rent-roll", "arrears"])
def test_reports_do_not_leak_portfolios_or_allow_tenants(dataset, report):
    org, client, lease, _ = dataset
    url = f"/api/v1/reports/{report}/"
    assert APIClient().get(url).status_code in (401, 403)
    tenant = member_client(org, "tenant", "report-tenant")
    assert tenant.get(url).status_code == 403
    other = Organization.objects.create(name="Other report portfolio")
    other_client = member_client(other, "owner", "report-outsider")
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
