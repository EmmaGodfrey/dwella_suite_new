# ruff: noqa: F811
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.billing.services import create_invoice
from apps.billing.tests import make_lease
from apps.organizations.models import Organization

from .models import OperationalDelivery, OperationalScan, ReminderPreferences
from .operational import enqueue, schedule_operational
from .test_operational import house  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("source", ["invoices", "leases"])
@pytest.mark.parametrize("failure", ["invalid_hour", "enqueue", "database"])
def test_bad_record_does_not_block_timezone_scan_or_next_page(house, source, failure, caplog):
    org, _, _, bad_lease, bad_invoice = house
    now = timezone.now().replace(hour=12)
    other = Organization.objects.create(name="Healthy schedule", timezone=org.timezone)
    good_lease = make_lease(other)
    good_lease.tenant.email = "healthy@example.com"
    good_lease.tenant.save(update_fields=["email"])
    if source == "invoices":
        for lease in (bad_lease, good_lease):
            lease.end_date = now.date() + timedelta(days=60)
            lease.save(update_fields=["end_date"])
        good = create_invoice(
            organization=other, tenant=good_lease.tenant, lease=good_lease,
            issue_date=now.date(), due_date=now.date(),
            lines=[{"kind": "rent", "description": "Rent", "amount": 100}],
        )
        bad, event = bad_invoice, "invoice.reminder"
    else:
        bad_invoice.status = "void"
        bad_invoice.save(update_fields=["status"])
        for lease in (bad_lease, good_lease):
            lease.end_date = now.date() + timedelta(days=30)
            lease.save(update_fields=["end_date"])
        bad, good, event = bad_lease, good_lease, "lease.expiry"
    if failure == "invalid_hour":
        # Data can predate validation or be written outside a form.
        ReminderPreferences.objects.create(organization=org, due_hour=25)
    OperationalDelivery.objects.all().delete()

    def send(target, *args, **kwargs):
        if target.pk == bad.pk and target._meta.label_lower == bad._meta.label_lower:
            if failure == "enqueue":
                raise ValueError("Malformed record")
            if failure == "database":
                enqueue(target, *args, **kwargs)
                # Fail after a partial insert; the savepoint must remove it and
                # preserve the enclosing scan transaction on PostgreSQL too.
                OperationalDelivery.objects.create(identity="invalid-missing-organization")
        return enqueue(target, *args, **kwargs)

    with patch("apps.notifications.operational.enqueue", side_effect=send):
        assert schedule_operational(limit=1, now=now) == 0
        scan = OperationalScan.objects.get(source=f"{source}:{org.timezone}")
        assert scan.after_id == bad.pk and not scan.completed
        assert schedule_operational(limit=1, now=now) == 1
        assert schedule_operational(limit=1, now=now) == 0
        assert schedule_operational(limit=1, now=now) == 0
    assert list(OperationalDelivery.objects.filter(event=event).values_list(
        "target_id", flat=True,
    )) == [good.pk]
    scan.refresh_from_db()
    assert scan.after_id == good.pk and scan.completed
    assert caplog.text.count("Operational scan skipped") == 1
    assert f"source={source} target_id={bad.pk}" in caplog.text
