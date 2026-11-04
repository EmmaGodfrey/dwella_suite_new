# ruff: noqa: F811
import csv
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Payment
from apps.billing.opening import record_deposit_held, record_opening_balance, set_rent_paid_up_to
from apps.billing.services import record_payment, void_invoice
from apps.billing.tests import make_lease
from apps.organizations.models import Organization, OrganizationMembership
from apps.reports.common import ReportExportThrottle
from apps.reports.test_activity import ledger  # noqa: F401
from apps.subscriptions.models import WorkspaceAccessPolicy

from .tests import account

pytestmark = pytest.mark.django_db
BASE = "/api/v1/portal/statements/"


@pytest.fixture
def portal_ledger(ledger):
    org, manager, lease, params, _, _, _ = ledger
    user, client = account(org, "tenant", "statement-tenant")
    lease.tenant.user = user
    lease.tenant.save(update_fields=["user"])
    return {
        "org": org, "manager": manager, "lease": lease, "tenant": lease.tenant,
        "user": user, "client": client, "params": params,
        "url": f"{BASE}{lease.tenant.public_id}/",
    }


def payload(response):
    assert response.status_code == 200, response.content
    return response.json()["response_data"]


def csv_rows(response):
    assert response.status_code == 200
    return list(csv.DictReader(StringIO(
        b"".join(response.streaming_content).decode("utf-8-sig"),
    )))


def test_portal_statement_matches_manager_ledger_and_lists_only_own_accounts(portal_ledger):
    ctx = portal_ledger
    make_lease(ctx["org"], unit_name="Private neighbour", phone="+260975551111")
    accounts = ctx["client"].get(BASE)
    assert payload(accounts) == [{"id": str(ctx["tenant"].public_id),
                                  "name": ctx["tenant"].full_name}]
    assert accounts.json()["pagination"]["count"] == 1
    response = ctx["client"].get(ctx["url"], ctx["params"])
    manager = ctx["manager"].get("/api/v1/reports/tenant-statement/", {
        **ctx["params"], "tenant": str(ctx["tenant"].public_id),
    })
    assert payload(response) == payload(manager)
    assert payload(response)["totals"]["closing_balance"] == "240.65"
    assert response.json()["pagination"]["count"] == 3
    assert response["Cache-Control"] == accounts["Cache-Control"] == "private, no-store"
    assert "national_id" not in str(payload(response))
    assert "notes" not in str(payload(response))
    assert ctx["client"].get("/api/v1/reports/tenant-statement/", {
        **ctx["params"], "tenant": str(ctx["tenant"].public_id),
    }).status_code == 403


def test_statement_pages_and_csv_preserve_exact_balances(portal_ledger):
    ctx = portal_ledger
    params = ctx["params"]
    pages = [payload(ctx["client"].get(ctx["url"], {**params, "page_size": 1, "page": page}))
             for page in (1, 2, 3)]
    assert [p["page_opening_balance"] for p in pages] == ["60.15", "260.50", "310.70"]
    response = ctx["client"].get(ctx["url"], {**params, "export": "csv"})
    assert response["Cache-Control"] == "private, no-store"
    assert "attachment;" in response["Content-Disposition"]
    rows = csv_rows(response)
    assert rows[0]["balance"] == "60.15" and rows[-1]["balance"] == "240.65"
    assert [row["balance"] for row in rows[1:-1]] == [p["rows"][0]["balance"] for p in pages]


def test_multiple_linked_records_remain_separate_statements(portal_ledger):
    ctx = portal_ledger
    second = make_lease(ctx["org"], unit_name="Second home", phone="+260975552222")
    second.tenant.user = ctx["user"]
    second.tenant.save(update_fields=["user"])
    accounts = payload(ctx["client"].get(BASE))
    assert {row["id"] for row in accounts} == {
        str(ctx["tenant"].public_id), str(second.tenant.public_id),
    }
    statement = payload(ctx["client"].get(f"{BASE}{second.tenant.public_id}/", ctx["params"]))
    assert statement["tenant"]["id"] == str(second.tenant.public_id)
    assert statement["rows"] == [] and statement["totals"]["closing_balance"] == "0.00"


def test_archived_record_is_hidden_even_with_another_active_link(portal_ledger):
    ctx = portal_ledger
    second = make_lease(ctx["org"], unit_name="Active link", phone="+260975554444")
    second.tenant.user = ctx["user"]
    second.tenant.save(update_fields=["user"])
    ctx["tenant"].is_active = False
    ctx["tenant"].save(update_fields=["is_active"])
    assert payload(ctx["client"].get(BASE)) == [{
        "id": str(second.tenant.public_id), "name": second.tenant.full_name,
    }]
    assert ctx["client"].get(ctx["url"]).status_code == 404


def test_statement_routes_reject_writes_and_malformed_ids(portal_ledger):
    ctx = portal_ledger
    assert ctx["client"].get(BASE + "not-a-uuid/").status_code == 404
    for url in (BASE, ctx["url"]):
        assert ctx["client"].post(url, {}, format="json").status_code == 405


def test_opening_debt_and_its_payment_use_the_same_portal_statement_ledger(portal_ledger):
    ctx = portal_ledger
    since = timezone.localdate() - timedelta(days=11)
    invoice = record_opening_balance(ctx["lease"], amount=Decimal("123.45"), owed_since=since)
    payment = record_payment(invoice=invoice, amount=Decimal("23.45"), method="cash",
                             paid_on=timezone.localdate())
    response = payload(ctx["client"].get(ctx["url"], ctx["params"]))
    assert response["totals"] == {
        "opening_balance": "183.60", "charges": "250.55", "payments": "93.50",
        "closing_balance": "340.65",
    }
    assert any(row["id"] == str(payment.public_id) for row in response["rows"])
    rows = csv_rows(ctx["client"].get(ctx["url"], {**ctx["params"], "export": "csv"}))
    assert rows[0]["balance"] == "183.60" and rows[-1]["balance"] == "340.65"


def test_opening_charge_in_period_is_restated_away_after_voiding(portal_ledger):
    ctx = portal_ledger
    invoice = record_opening_balance(ctx["lease"], amount=Decimal("123.45"),
                                     owed_since=timezone.localdate())
    before = payload(ctx["client"].get(ctx["url"], ctx["params"]))
    assert before["totals"]["charges"] == "374.00"
    assert any(row["id"] == str(invoice.public_id) for row in before["rows"])
    void_invoice(invoice)
    after = payload(ctx["client"].get(ctx["url"], ctx["params"]))
    assert after["totals"]["charges"] == "250.55"
    assert after["totals"]["closing_balance"] == "240.65"
    assert not any(row["id"] == str(invoice.public_id) for row in after["rows"])


def test_paid_ahead_months_and_deposit_held_do_not_invent_statement_payments(portal_ledger):
    ctx = portal_ledger
    before = payload(ctx["client"].get(ctx["url"], ctx["params"]))
    set_rent_paid_up_to(ctx["lease"], timezone.localdate().replace(day=1))
    record_deposit_held(ctx["lease"], amount=Decimal("1000"), occurred_on=timezone.localdate(),
                         user=ctx["manager"].handler._force_user)
    after = payload(ctx["client"].get(ctx["url"], ctx["params"]))
    assert after == before


@pytest.mark.parametrize("export", [False, True])
def test_other_tenant_and_workspace_and_unknown_ids_are_indistinguishable(portal_ledger, export):
    ctx = portal_ledger
    neighbour = make_lease(ctx["org"], unit_name="Neighbour", phone="+260975553333")
    other = make_lease(Organization.objects.create(name="Other workspace"))
    # Even linking the same login does not allow crossing the current workspace boundary.
    other.tenant.user = ctx["user"]
    other.tenant.save(update_fields=["user"])
    params = {**ctx["params"], **({"export": "csv"} if export else {})}
    responses = [ctx["client"].get(f"{BASE}{key}/", params)
                 for key in (neighbour.tenant.public_id, other.tenant.public_id, uuid4())]
    assert all(row.status_code == 404 for row in responses)
    assert responses[0].json() == responses[1].json() == responses[2].json()
    assert all(row["Cache-Control"] == "private, no-store" for row in responses)


@pytest.mark.parametrize("endpoint", ["list", "detail"])
def test_statement_requires_authenticated_linked_tenant_role(portal_ledger, endpoint):
    ctx = portal_ledger
    url = BASE if endpoint == "list" else ctx["url"]
    assert APIClient().get(url).status_code in {401, 403}
    assert ctx["manager"].get(url).status_code == 403
    _, unlinked = account(ctx["org"], "tenant", "statement-unlinked")
    assert unlinked.get(url).status_code == 403
    ctx["user"].is_staff = True
    ctx["user"].save(update_fields=["is_staff"])
    assert ctx["client"].get(url).status_code == 403


@pytest.mark.parametrize("failure", ["unlink", "archive", "membership", "suspend", "feature"])
def test_statement_rechecks_portal_access_after_prior_success(portal_ledger, failure):
    ctx = portal_ledger
    assert ctx["client"].get(ctx["url"]).status_code == 200
    if failure == "unlink":
        ctx["tenant"].user = None
        ctx["tenant"].save(update_fields=["user"])
    elif failure == "archive":
        ctx["tenant"].is_active = False
        ctx["tenant"].save(update_fields=["is_active"])
    elif failure == "membership":
        OrganizationMembership.objects.filter(user=ctx["user"]).update(is_active=False)
    elif failure == "suspend":
        ctx["org"].is_active = False
        ctx["org"].save(update_fields=["is_active"])
    else:
        WorkspaceAccessPolicy.objects.create(organization=ctx["org"], feature_overrides={
            "tenant_portal": {"enabled": False},
        })
    for url in (BASE, ctx["url"]):
        response = ctx["client"].get(url)
        assert response.status_code == 403
        assert response["Cache-Control"] == "private, no-store"


@pytest.mark.parametrize("params", [
    {"date_from": "nonsense"}, {"date_to": "2099-01-01"},
    {"date_from": "2020-01-01", "date_to": "2019-01-01"},
    {"date_from": "2020-01-01", "date_to": "2022-01-01"},
    {"page": 0}, {"page_size": 101}, {"page": 999}, {"export": "pdf"},
    {"tenant": str(uuid4())}, {"property": str(uuid4())}, {"as_of": "2020-01-01"},
])
def test_statement_rejects_invalid_ranges_limits_and_scope_filters(portal_ledger, params):
    ctx = portal_ledger
    response = ctx["client"].get(ctx["url"], params)
    assert response.status_code == 400
    assert not response.json()["success"]
    assert response["Cache-Control"] == "private, no-store"


def test_empty_period_and_export_do_not_drop_opening_balance(portal_ledger):
    ctx = portal_ledger
    params = {"date_from": str(timezone.localdate()), "date_to": str(timezone.localdate())}
    statement = payload(ctx["client"].get(ctx["url"], params))
    assert statement["rows"] == []
    assert statement["totals"]["opening_balance"] == "240.65"
    assert statement["totals"]["closing_balance"] == "240.65"
    ctx["tenant"].full_name = "=SUM(1,2)"
    ctx["tenant"].save(update_fields=["full_name"])
    rows = csv_rows(ctx["client"].get(ctx["url"], {**params, "export": "csv"}))
    assert len(rows) == 2 and rows[-1]["balance"] == "240.65"
    assert all(row["tenant"].startswith("'=SUM") for row in rows)


def test_statement_export_is_throttled_without_blocking_json(portal_ledger, monkeypatch):
    ctx = portal_ledger
    key = f"throttle_report_export_{ctx['user'].pk}"
    cache.delete(key)
    monkeypatch.setattr(ReportExportThrottle, "rate", "1/hour")
    try:
        assert csv_rows(ctx["client"].get(ctx["url"], {"export": "csv"}))
        assert ctx["client"].get(ctx["url"], {"export": "csv"}).status_code == 429
        assert ctx["client"].get(ctx["url"]).status_code == 200
    finally:
        cache.delete(key)


def test_statement_query_budget_is_constant_for_one_and_full_page_and_stream(portal_ledger):
    ctx = portal_ledger

    def cost(**extra):
        with CaptureQueriesContext(connection) as captured:
            response = ctx["client"].get(ctx["url"], {**ctx["params"], **extra})
            if response.streaming:
                assert csv_rows(response)
            else:
                assert payload(response)
        return len(captured)

    small = cost(page_size=1), cost(export="csv")
    invoice = ctx["lease"].invoices.first()
    Payment.objects.bulk_create([
        Payment(organization=ctx["org"], tenant=ctx["tenant"], invoice=invoice,
                receipt_number=f"RCT-PORTAL-BUDGET-{index}", amount=Decimal("1"), method="cash",
                paid_on=timezone.localdate() - timedelta(days=1)) for index in range(99)
    ])
    full = cost(page_size=100), cost(export="csv")
    assert small == full
    assert cost(page_size=1, page=2) <= small[0] + 2
    print(f"PORTAL_STATEMENT_QUERY_BUDGET small={small}, full={full} (JSON, consumed CSV)")
