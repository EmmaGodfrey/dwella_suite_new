# ruff: noqa: F811
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.billing.tests import member_client
from apps.maintenance.models import MaintenanceRequest, Vendor
from apps.organizations.models import Organization
from apps.portal.tests import home  # noqa: F401

pytestmark = pytest.mark.django_db
URL = "/api/v1/properties/dashboard/"


def test_dashboard_counts_only_current_workspace_open_active_requests(home):
    manager = member_client(home["org"], "landlord", "dashboard-repairs-manager")
    prop = home["lease"].unit.property
    vendor = Vendor.objects.create(organization=home["org"], name="Repair team")
    for i, status in enumerate(["new", "scheduled", "in_progress", "completed", "cancelled"]):
        MaintenanceRequest.objects.create(
            organization=home["org"],
            property=prop,
            reference=f"DASH-{i}",
            title="Tap",
            status=status,
            priority="urgent" if i == 0 else "normal",
            vendor=vendor if i in [1, 2] else None,
        )
    MaintenanceRequest.objects.create(
        organization=home["org"],
        property=prop,
        reference="DASH-INACTIVE",
        title="Archived",
        is_active=False,
    )
    other = Organization.objects.create(name="Other repairs portfolio")
    MaintenanceRequest.objects.create(
        organization=other, property=prop, reference="DASH-OTHER", title="Foreign repair"
    )
    data = manager.get(URL).json()["response_data"]
    assert data["repairs"] == {"open": 3, "urgent": 1, "unassigned": 1}
    opened = manager.get("/api/v1/maintenance/requests/?open=true").json()
    assert opened["pagination"]["count"] == 3
    assert {row["status"] for row in opened["response_data"]} == {"new", "scheduled", "in_progress"}
    assert home["client"].get(URL).status_code == 403


def test_dashboard_repair_query_count_stays_constant(home):
    manager = member_client(home["org"], "landlord", "dashboard-repairs-query")
    with CaptureQueriesContext(connection) as small:
        assert manager.get(URL).status_code == 200
    MaintenanceRequest.objects.bulk_create(
        [
            MaintenanceRequest(
                organization=home["org"],
                property=home["lease"].unit.property,
                reference=f"DASH-{i}",
                title="Repair",
            )
            for i in range(100)
        ]
    )
    with CaptureQueriesContext(connection) as full:
        data = manager.get(URL).json()["response_data"]
    assert data["repairs"]["open"] == 100
    assert len(full) == len(small)
