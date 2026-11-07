import pytest
from django.db import connection

pytestmark = pytest.mark.django_db


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL row security required")
def test_fresh_operational_migration_protects_all_private_tables():
    tables = {
        "notifications_operationaldelivery", "notifications_operationalscan",
        "notifications_notificationphonelink",
    }
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relname, relrowsecurity FROM pg_class WHERE relname = ANY(%s)",
            [sorted(tables)],
        )
        assert dict(cursor.fetchall()) == dict.fromkeys(tables, True)
