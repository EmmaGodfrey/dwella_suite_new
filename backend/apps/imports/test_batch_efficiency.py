import pytest

from apps.organizations.models import Organization
from apps.tenants.models import Tenant

from .importers import TenantImporter
from .services import check

pytestmark = pytest.mark.django_db


def test_tenant_batch_lookup_is_bounded_and_refreshed(django_assert_num_queries):
    org = Organization.objects.create(name="Batch efficiency")
    importer = TenantImporter(org)
    rows = [
        (i + 2, {"full_name": f"Person {i}", "phone_number": f"097{i:07d}"})
        for i in range(500)
    ]
    with django_assert_num_queries(1):
        result = check(importer, rows)
    assert all(item["status"] == "ready" for item in result)
    other = Organization.objects.create(name="Separate import workspace")
    Tenant.objects.create(organization=other, full_name="Other", phone_number="+260970000001")
    Tenant.objects.create(
        organization=org, full_name="Archived", phone_number="+260970000000", is_active=False
    )
    # Confirmation must see records added since preview, even if the importer is reused.
    with django_assert_num_queries(1):
        refreshed = check(importer, rows)
    assert refreshed[0]["status"] == "duplicate"
    assert all(item["status"] == "ready" for item in refreshed[1:])
