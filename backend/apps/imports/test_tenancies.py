import csv
from io import BytesIO, StringIO
from zipfile import ZipFile

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.billing.models import Invoice
from apps.billing.tests import member_client
from apps.leases.models import Lease
from apps.organizations.models import Organization
from apps.properties.models import Property, Unit
from apps.subscriptions.models import WorkspaceAccessPolicy
from apps.tenants.models import Tenant

pytestmark = pytest.mark.django_db
BASE = "/api/v1/tenants/"
HEADERS = [
    "property",
    "unit",
    "rent_amount",
    "full_name",
    "phone_number",
    "tpin",
    "national_id",
    "billing_address",
    "lease_start",
    "lease_end",
]


@pytest.fixture
def portfolio():
    org = Organization.objects.create(name="Combined import")
    Property.objects.create(organization=org, name="Court", address="Plot 1")
    return org, member_client(org, "landlord", "combined-manager")


def text(rows):
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(HEADERS)
    writer.writerows(rows)
    return stream.getvalue()


def row(index=1):
    return [
        "Court",
        f"Unit {index}",
        "3500",
        f"Tenant {index}",
        f"097{index:07d}",
        "0123456789",
        "123456/10/1",
        "Plot 1",
        "2026-11-01",
        "2027-10-31",
    ]


def preview(client, rows):
    return client.post(BASE + "import-preview/?kind=tenancies", {"csv": text(rows)}, format="json")


def confirm(client, token):
    return client.post(
        BASE + "import-confirm/?kind=tenancies", {"preview_token": token}, format="json"
    )


def test_combined_preview_and_atomic_draft_import(portfolio):
    org, client = portfolio
    response = preview(client, [row(), ["Court", "Vacant", "2500"]])
    assert response.status_code == 200, response.content
    body = response.json()["response_data"]
    assert body["counts"]["ready"] == 2
    assert not Unit.objects.exists()
    token = body["preview_token"]
    assert len(token) == 43 and "0123456789" not in token
    encrypted = cache.get(f"portfolio-import-preview:{token}")
    assert "0123456789" not in encrypted and "Tenant 1" not in encrypted
    result = confirm(client, token)
    assert result.status_code == 201, result.content
    assert Unit.objects.count() == 2
    tenant = Tenant.objects.get(organization=org)
    assert tenant.tpin == "0123456789"
    lease = Lease.objects.get()
    assert lease.tenant == tenant and lease.unit.name == "Unit 1"
    assert lease.status == "draft" and tenant.status == "applicant"
    assert not Invoice.objects.exists()
    assert confirm(client, token).status_code == 400


def test_links_existing_records_without_overwriting_and_blocks_conflicts(portfolio):
    org, client = portfolio
    unit = Unit.objects.create(
        organization=org, property=Property.objects.get(), name="Unit 1", rent_amount=1
    )
    tenant = Tenant.objects.create(
        organization=org, full_name="Tenant 1", phone_number="+260970000001"
    )
    token = preview(client, [row()]).json()["response_data"]["preview_token"]
    assert confirm(client, token).status_code == 201
    assert Tenant.objects.count() == Unit.objects.count() == 1
    unit.refresh_from_db()
    assert unit.rent_amount == 1 and tenant.tpin == ""
    assert Lease.objects.get().tenant == tenant
    again = preview(client, [row()]).json()["response_data"]
    assert again["counts"]["duplicate"] == 1


def test_scope_capacity_changes_and_expiry_fail_without_partial_writes(portfolio):
    org, client = portfolio
    body = preview(client, [row()]).json()["response_data"]
    token = body["preview_token"]
    other = member_client(org, "landlord", "other-manager")
    assert confirm(other, token).status_code == 400
    outside = Organization.objects.create(name="Outside")
    assert confirm(member_client(outside, "landlord", "outsider"), token).status_code == 400
    WorkspaceAccessPolicy.objects.create(organization=org, limits={"tenants": 0})
    assert confirm(client, token).status_code != 201
    assert not Unit.objects.exists() and not Lease.objects.exists()
    cache.delete(f"portfolio-import-preview:{token}")
    assert confirm(client, token).status_code == 400
    assert confirm(client, "bad token").status_code == 400


def test_incomplete_details_flagged_and_repeated_identity_conflicts_reviewed(portfolio):
    _, client = portfolio
    incomplete = row()
    incomplete[5] = ""
    result = preview(client, [incomplete]).json()["response_data"]
    assert {item["field"] for item in result["rows"][0]["missing_details"]} == {"tpin"}
    assert confirm(client, result["preview_token"]).status_code == 201
    second, third = row(2), row(3)
    third[4] = second[4]
    result = preview(client, [second, third]).json()["response_data"]
    assert result["counts"]["duplicate"] == 2


def test_import_permissions_and_throttling(portfolio, settings):
    org, client = portfolio
    assert preview(APIClient(), [row()]).status_code in (401, 403)
    assert preview(member_client(org, "tenant", "tenant-role"), [row()]).status_code == 403
    from unittest.mock import patch

    from apps.imports.views import ImportThrottle

    with patch.object(ImportThrottle, "rate", "1/hour"):
        cache.clear()
        assert preview(client, [row()]).status_code == 200
        assert preview(client, [row()]).status_code == 429


def test_combined_preview_select_count_is_bounded(portfolio):
    _, client = portfolio
    counts = []
    for size in [10, 500]:
        with CaptureQueriesContext(connection) as captured:
            response = preview(client, [row(index) for index in range(1, size + 1)])
        assert response.status_code == 200
        counts.append(sum(query["sql"].lstrip().upper().startswith("SELECT") for query in captured))
    assert counts[1] == counts[0]


def test_combined_confirmation_uses_batched_writes_and_bounded_selects(portfolio):
    _, client = portfolio
    from time import perf_counter

    metrics = []
    for size, offset in [(10, 1000), (500, 2000)]:
        token = preview(client, [row(index + offset) for index in range(size)]).json()[
            "response_data"
        ]["preview_token"]
        started = perf_counter()
        with CaptureQueriesContext(connection) as captured:
            response = confirm(client, token)
        assert response.status_code == 201, response.content
        selects = sum(query["sql"].lstrip().upper().startswith("SELECT") for query in captured)
        inserts = sum(query["sql"].lstrip().upper().startswith("INSERT") for query in captured)
        metrics.append(
            {
                "rows": size,
                "selects": selects,
                "inserts": inserts,
                "seconds": round(perf_counter() - started, 3),
            }
        )
    assert metrics[0]["selects"] == metrics[1]["selects"]
    assert metrics[1]["inserts"] < 40
    print("COMBINED_IMPORT_METRICS", metrics)


def excel(cells):
    stream = BytesIO()
    with ZipFile(stream, "w") as book:
        book.writestr(
            "xl/workbook.xml",
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
        )
        book.writestr(
            "xl/worksheets/sheet1.xml",
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
            + cells
            + "</sheetData></worksheet>",
        )
    return SimpleUploadedFile("portfolio.xlsx", stream.getvalue())


def test_excel_text_identity_preservation_and_formula_rejection(portfolio):
    _, client = portfolio
    from xml.sax.saxutils import escape

    xml = ""
    for number, values in enumerate([HEADERS, row()], 1):
        xml += (
            "<row>"
            + "".join(
                f'<c r="{chr(65+i)}{number}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
                for i, value in enumerate(values)
            )
            + "</row>"
        )
    response = client.post(BASE + "import-preview/?kind=tenancies", {"file": excel(xml)})
    assert response.status_code == 200, response.content
    assert response.json()["response_data"]["rows"][0]["values"]["tpin"] == "0123456789"
    bad = excel('<row><c r="A1"><f>WEBSERVICE("https://example.com")</f><v>1</v></c></row>')
    assert client.post(BASE + "import-preview/?kind=tenancies", {"file": bad}).status_code == 400


def test_changed_match_is_not_silently_linked(portfolio):
    org, client = portfolio
    token = preview(client, [row()]).json()["response_data"]["preview_token"]
    Unit.objects.create(
        organization=org, property=Property.objects.get(), name="Unit 1", rent_amount=1
    )
    response = confirm(client, token)
    assert response.status_code == 400
    assert not Tenant.objects.exists() and not Lease.objects.exists()


def test_excel_rejects_numeric_ids_entities_and_expansion_bombs(portfolio):
    _, client = portfolio
    from zipfile import ZIP_DEFLATED

    numeric = excel(
        '<row><c r="A1" t="inlineStr"><is><t>tpin</t></is></c></row>'
        '<row><c r="A2"><v>123456789</v></c></row>'
    )
    response = client.post(BASE + "import-preview/?kind=tenancies", {"file": numeric})
    assert response.status_code == 400 and b"Text" in response.content
    entities = excel('<!DOCTYPE x [<!ENTITY y "unsafe">]>')
    assert (
        client.post(BASE + "import-preview/?kind=tenancies", {"file": entities}).status_code == 400
    )
    stream = BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED) as book:
        book.writestr("xl/worksheets/sheet1.xml", "x" * 8_000_001)
    bomb = SimpleUploadedFile("large.xlsx", stream.getvalue())
    response = client.post(BASE + "import-preview/?kind=tenancies", {"file": bomb})
    assert response.status_code == 400 and b"expands" in response.content
