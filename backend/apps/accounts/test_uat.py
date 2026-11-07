import csv
import io
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, connections
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from .access_state import mark_email_verified
from .models import TwoFactorDevice, UatResult
from .uat import BY_ID, CAMPAIGN, CASES, UatExportThrottle, UatWriteThrottle

pytestmark = pytest.mark.django_db
BASE = "/api/v1/accounts/uat/"
FLOW = "ACC-01"


@pytest.fixture(autouse=True)
def policy(settings):
    settings.APP_ENVIRONMENT = "test"
    settings.ALPHA_TEST_ENABLED = True
    settings.REQUIRE_ADMIN_MFA = False
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    user = get_user_model().objects.create_user(username="uat", email="uat@example.com")
    mark_email_verified(user)
    return user


def client(user=None):
    api = APIClient()
    if user:
        api.force_authenticate(user)
    return api


def write(api, payload, case=FLOW):
    return api.patch(f"{BASE}results/{case}/", payload, format="json")


def test_uat_is_authenticated_test_only_and_no_store(user, settings):
    assert client().get(BASE).status_code == 403
    assert write(client(), {"status": "passed"}).status_code == 403
    assert client().get(BASE + "export/").status_code == 403
    api = client(user)
    response = api.get(BASE)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    settings.ALPHA_TEST_ENABLED = False
    assert api.get(BASE).status_code == 404
    assert write(api, {"status": "passed"}).status_code == 404
    settings.ALPHA_TEST_ENABLED = True
    settings.APP_ENVIRONMENT = "production"
    assert api.get(BASE).status_code == 404


def test_catalogue_covers_participants_and_excludes_administrator_workflows(user):
    data = client(user).get(BASE).json()["response_data"]
    assert len(data["cases"]) == 131
    assert {"ACC-16", "LEASE-09", "LEASE-10", "LEASE-11"} <= BY_ID.keys()
    assert len(BY_ID) == len(CASES)
    assert not any(row["id"].startswith("ADM-") for row in data["cases"])
    assert all(set(row["roles"]) <= {"manager", "tenant"} for row in data["cases"])
    modules = {
        "WhatsApp", "Invoices", "Maintenance", "Reports", "Accounts", "Assistant", "Deposits",
    }
    assert modules <= {
        row["module"] for row in data["cases"]
    }
    assert data["results"] == [] and not data["can_export"]


@pytest.mark.parametrize("status", UatResult.Status.values)
def test_all_results_persist_and_default_does_not_imply_passed(user, status):
    response = write(client(user), {"status": status})
    assert response.status_code == 200
    result = response.json()["response_data"]
    assert result["status"] == status
    assert result["case_id"] == FLOW
    assert "user" not in result
    assert client(user).get(BASE).json()["response_data"]["results"][0]["status"] == status


def test_partial_updates_preserve_other_fields_and_identical_save_is_noop(user):
    api = client(user)
    assert write(api, {"notes": "<script>literal error example</script>"}).status_code == 200
    assert write(api, {"status": "partial"}).status_code == 200
    row = UatResult.objects.get()
    stamp = row.updated_at
    assert row.notes == "<script>literal error example</script>"
    assert write(api, {"status": "partial"}).status_code == 200
    row.refresh_from_db()
    assert row.updated_at == stamp and UatResult.objects.count() == 1
    assert write(api, {"notes": ""}).status_code == 200
    row.refresh_from_db()
    assert row.notes == "" and row.status == "partial"


@pytest.mark.parametrize("payload", [
    {}, [], "bad", {"status": "done"}, {"status": None}, {"notes": "a" * 2001},
    {"status": "passed", "user_id": 123}, {"campaign": "other"}, {"notes": ["bad"]},
])
def test_invalid_and_foreign_input_cannot_create_results(user, payload):
    assert write(client(user), payload).status_code == 400
    assert not UatResult.objects.exists()


@pytest.mark.parametrize("case", ["ADM-01", "unknown", "ACC-999"])
def test_unknown_or_administrator_case_is_not_writable(user, case):
    assert write(client(user), {"status": "passed"}, case).status_code == 404
    assert not UatResult.objects.exists()


def test_results_are_private_and_campaign_scoped(user):
    other = get_user_model().objects.create_user(username="other", email="other@example.com")
    mark_email_verified(other)
    assert write(client(user), {"status": "failed", "notes": "private"}).status_code == 200
    UatResult.objects.create(user=user, campaign="old", case_id=FLOW, status="passed")
    assert client(other).get(BASE).json()["response_data"]["results"] == []
    assert write(client(other), {"status": "passed"}).status_code == 200
    assert UatResult.objects.get(user=user, campaign=CAMPAIGN).status == "failed"
    assert len(client(user).get(BASE).json()["response_data"]["results"]) == 1
    assert client(user).get(BASE + "export/").status_code == 403


@pytest.mark.parametrize("change", ["email", "inactive"])
def test_unverified_changed_or_inactive_identity_cannot_save(user, change):
    if change == "email":
        user.email = "changed@example.com"
    else:
        user.is_active = False
    user.save()
    assert write(client(user), {"status": "passed"}).status_code == 403
    assert not UatResult.objects.exists()


@pytest.mark.parametrize("role", ["staff", "superuser"])
def test_export_requires_admin_and_mfa_and_escapes_formula_cells(user, settings, role):
    api = client(user)
    assert write(api, {"notes": "=HYPERLINK(\"example\")", "status": "failed"}).status_code == 200
    user.is_staff = role == "staff"
    user.is_superuser = role == "superuser"
    user.save(update_fields=["is_staff", "is_superuser"])
    settings.REQUIRE_ADMIN_MFA = True
    assert api.get(BASE + "export/").status_code == 403
    TwoFactorDevice.objects.create(user=user, secret="JBSWY3DPEHPK3PXP", is_confirmed=True)
    response = api.get(BASE + "export/")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert rows[0]["Note"].startswith("'=HYPERLINK")
    assert rows[0]["Email"] == user.email
    assert write(api, {"status": "passed"}).status_code == 403
    assert api.get(BASE + "export/?tester=invalid").status_code == 400
    assert api.get(BASE + "export/?email=invalid").status_code == 400


def test_read_queries_do_not_grow_per_result(user):
    api = client(user)
    write(api, {"status": "passed"})
    with CaptureQueriesContext(connection) as small:
        assert len(api.get(BASE).data["results"]) == 1
    UatResult.objects.bulk_create([
        UatResult(user=user, campaign=CAMPAIGN, case_id=case_id, status="partial")
        for case_id in BY_ID if case_id != FLOW
    ])
    with CaptureQueriesContext(connection) as full:
        assert len(api.get(BASE).data["results"]) == len(CASES)
    assert len(small) == len(full)


def test_result_updates_are_throttled(user, monkeypatch):
    monkeypatch.setattr(UatWriteThrottle, "rate", "2/min")
    api = client(user)
    assert write(api, {"status": "passed"}).status_code == 200
    assert write(api, {"status": "partial"}).status_code == 200
    assert write(api, {"status": "failed"}).status_code == 429


def test_export_is_bounded_and_can_be_filtered_to_one_tester(user):
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    people = get_user_model().objects.bulk_create([
        get_user_model()(username=f"participant-{i}", email=f"p{i}@example.com")
        for i in range(39)
    ])
    UatResult.objects.bulk_create([
        UatResult(user=person, campaign=CAMPAIGN, case_id=case_id, status="partial")
        for person in people for case_id in BY_ID
    ])
    api = client(user)
    assert api.get(BASE + "export/").status_code == 400
    response = api.get(BASE + f"export/?tester={people[0].pk}")
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert len(rows) == len(CASES)
    assert {row["Email"] for row in rows} == {people[0].email}
    response = api.get(BASE + "export/", {"email": people[0].email})
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert len(rows) == len(CASES)
    assert {row["Email"] for row in rows} == {people[0].email}


def test_staff_exports_are_throttled(user, monkeypatch):
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    monkeypatch.setattr(UatExportThrottle, "rate", "1/min")
    api = client(user)
    assert api.get(BASE + "export/").status_code == 200
    assert api.get(BASE + "export/").status_code == 429


@pytest.mark.django_db(transaction=True)
def test_concurrent_note_and_status_do_not_overwrite_one_another(user):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency requires PostgreSQL")
    UatResult.objects.create(user=user, campaign=CAMPAIGN, case_id=FLOW)
    barrier = Barrier(2)

    def save(payload):
        connections.close_all()
        try:
            barrier.wait(timeout=10)
            return write(client(user), payload).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(save, [{"notes": "new note"}, {"status": "partial"}]))
    assert statuses == [200, 200]
    row = UatResult.objects.get()
    assert row.notes == "new note" and row.status == "partial"
