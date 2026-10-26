# ruff: noqa: F811
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.access_state import require_new_account_verification
from apps.documents.models import DocumentVersion
from apps.maintenance.models import MaintenanceRequest, MaintenanceUpdate
from apps.portal.tests import account, home  # noqa: F401
from apps.subscriptions.models import WorkspaceAccessPolicy

from .models import NotificationPreferences, NotificationRead

pytestmark = pytest.mark.django_db
URL = "/api/v1/notifications/"


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()


def feed(home):
    response = home["client"].get(URL)
    assert response.status_code == 200, response.content
    assert response["Cache-Control"] == "private, no-store"
    return response.json()["response_data"]


def repair(home, *, tenant=None, reference="MR-NOTICE", **values):
    return MaintenanceRequest.objects.create(
        organization=home["org"],
        property=home["lease"].unit.property,
        unit=home["lease"].unit,
        tenant=tenant or home["lease"].tenant,
        reference=reference,
        title="Kitchen tap",
        **values,
    )


def test_tenant_sees_own_invoice_payment_lease_and_repair_notices(home):
    job = repair(home)
    home["lease"].end_date = timezone.localdate() + timedelta(days=10)
    home["lease"].save()
    data = feed(home)
    assert {row["kind"] for row in data["items"]} == {"arrears", "payment", "lease", "maintenance"}
    assert any(row["path"] == f"/maintenance/{job.public_id}" for row in data["items"])
    assert any(
        row["path"] == f"/billing?invoice={home['invoice'].public_id}" for row in data["items"]
    )
    assert data["unread_count"] == len(data["items"])


def test_notification_read_state_is_personal_and_foreign_ids_are_rejected(home):
    own = repair(home)
    neighbour = repair(home, tenant=home["neighbour"].tenant, reference="MR-PRIVATE")
    other_user, other_client = account(home["org"], "tenant", "notice-neighbour")
    home["neighbour"].tenant.user = other_user
    home["neighbour"].tenant.save()
    own_ids = [row["id"] for row in feed(home)["items"]]
    assert home["client"].post(URL, {"ids": own_ids}, format="json").status_code == 200
    assert feed(home)["unread_count"] == 0
    assert other_client.post(URL, {"ids": own_ids}, format="json").status_code == 400
    other_data = other_client.get(URL).json()["response_data"]
    assert other_data["unread_count"] > 0
    assert str(own.public_id) not in str(other_data)
    assert str(neighbour.public_id) not in str(feed(home))


def test_internal_notes_and_other_tenant_updates_are_never_returned(home):
    own = repair(home)
    other = repair(home, tenant=home["neighbour"].tenant, reference="MR-SECRET")
    MaintenanceUpdate.objects.create(request=own, body="INTERNAL SECRET", is_internal=True)
    MaintenanceUpdate.objects.create(request=other, body="NEIGHBOUR SECRET", is_internal=False)
    MaintenanceUpdate.objects.create(request=own, body="PRIVATE REPLY BODY", is_internal=False)
    data = feed(home)
    assert len([row for row in data["items"] if row["id"].startswith("repair_update:")]) == 1
    assert "SECRET" not in str(data) and "PRIVATE REPLY BODY" not in str(data)


def test_self_authored_comments_do_not_notify_the_sender(home):
    job = repair(home)
    MaintenanceUpdate.objects.create(request=job, body="My own reply", author=home["user"])
    assert not any(row["id"].startswith("repair_update:") for row in feed(home)["items"])


def test_new_comments_and_status_changes_become_unread(home):
    job = repair(home)
    ids = [row["id"] for row in feed(home)["items"]]
    assert home["client"].post(URL, {"ids": ids}, format="json").status_code == 200
    update = MaintenanceUpdate.objects.create(request=job, body="An update", is_internal=False)
    data = feed(home)
    assert data["unread_count"] == 1
    assert any(row["id"].endswith(f":{update.pk}") and not row["read"] for row in data["items"])
    job.status, job.completed_at = "completed", timezone.now()
    job.save()
    data = feed(home)
    assert data["unread_count"] == 2
    assert any(row["title"] == "Repair completed" and not row["read"] for row in data["items"])


@pytest.mark.parametrize(
    "change", ["unlinked", "archived", "membership", "suspended", "feature", "verification"]
)
def test_tenant_notifications_close_when_current_access_is_removed(home, change):
    ids = [row["id"] for row in feed(home)["items"]]
    if change in {"unlinked", "archived"}:
        tenant = home["lease"].tenant
        if change == "unlinked":
            tenant.user = None
        else:
            tenant.is_active = False
        tenant.save()
    elif change == "membership":
        home["user"].organization_memberships.update(is_active=False)
    elif change == "suspended":
        home["org"].is_active = False
        home["org"].save()
    elif change == "feature":
        WorkspaceAccessPolicy.objects.update_or_create(
            organization=home["org"], defaults={"feature_overrides": {"tenant_portal": False}}
        )
    else:
        require_new_account_verification(home["user"])
    assert home["client"].get(URL).status_code == 403
    assert home["client"].post(URL, {"ids": ids}, format="json").status_code == 403


def test_anonymous_and_unlinked_accounts_have_no_notification_access(home):
    assert APIClient().get(URL).status_code in {401, 403}
    assert APIClient().post(URL, {"ids": ["arbitrary"]}, format="json").status_code in {401, 403}
    _, unlinked = account(home["org"], "tenant", "notice-unlinked")
    assert unlinked.get(URL).status_code == 403


def test_preferences_hide_optional_notices_but_keep_overdue_rent(home):
    repair(home)
    NotificationPreferences.objects.create(
        user=home["user"], in_app_payment=False, in_app_lease=False, in_app_maintenance=False
    )
    assert {row["kind"] for row in feed(home)["items"]} == {"arrears"}


@pytest.mark.parametrize(
    "payload", [{}, {"ids": []}, {"ids": ["unknown"]}, {"ids": ["x" * 101]}, {"ids": ["x"] * 1001}]
)
def test_mark_read_rejects_malformed_or_invented_ids(home, payload):
    assert home["client"].post(URL, payload, format="json").status_code == 400
    assert not NotificationRead.objects.exists()


def test_mark_read_is_rate_limited(home):
    ids = [row["id"] for row in feed(home)["items"]]
    with patch("apps.notifications.views.NotificationReadThrottle.rate", "1/hour"):
        assert home["client"].post(URL, {"ids": ids}, format="json").status_code == 200
        assert home["client"].post(URL, {"ids": ids}, format="json").status_code == 429


def test_read_state_lookup_only_loads_keys_in_the_current_feed(home):
    NotificationRead.objects.bulk_create(
        [
            NotificationRead(organization=home["org"], user=home["user"], key=f"old:{i}")
            for i in range(30)
        ]
    )
    with CaptureQueriesContext(connection) as queries:
        feed(home)
    reads = [q["sql"] for q in queries if 'FROM "notifications_notificationread"' in q["sql"]]
    assert len(reads) == 1 and '"key" IN' in reads[0]


def test_tenant_feed_query_count_does_not_grow_per_row(home):
    job = repair(home)
    with CaptureQueriesContext(connection) as small:
        feed(home)
    MaintenanceUpdate.objects.bulk_create(
        [MaintenanceUpdate(request=job, body="Visible update") for _ in range(100)]
    )
    with CaptureQueriesContext(connection) as full:
        data = feed(home)
    assert len(data["items"]) >= 100
    assert len(full) == len(small)


def test_document_notices_exclude_private_versions_and_pdf_payloads(home):
    for version, status in enumerate(
        ["ready", "revoked", "superseded", "signing", "signed"], start=1
    ):
        DocumentVersion.objects.create(
            organization=home["org"],
            lease=home["lease"],
            kind="lease",
            version=version,
            status=status,
            snapshot={"private": "HIDDEN SNAPSHOT"},
            source_fingerprint="x" * 64,
            unsigned_pdf=b"PRIVATE PDF",
            pdf=b"PRIVATE PDF",
            sha256="x" * 64,
            page_count=1,
            created_by=home["user"],
        )
    with CaptureQueriesContext(connection) as queries:
        data = feed(home)
    docs = [row for row in data["items"] if row["id"].startswith("document:")]
    assert len(docs) == 2
    assert "PRIVATE PDF" not in str(data) and "HIDDEN SNAPSHOT" not in str(data)
    assert not any('"documents_documentversion"."pdf"' in q["sql"] for q in queries)
