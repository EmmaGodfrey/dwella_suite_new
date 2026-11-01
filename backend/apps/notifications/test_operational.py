from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Payment
from apps.billing.services import create_invoice, record_payment, reverse_payment
from apps.billing.tests import make_lease
from apps.common.email_router import EmailQuotaExceeded
from apps.maintenance.models import MaintenanceUpdate
from apps.maintenance.services import create_request, start_request
from apps.organizations.models import Organization, OrganizationMembership

from .models import (
    NotificationPhoneLink,
    NotificationPreferences,
    OperationalDelivery,
    OperationalScan,
    PhoneMessagingConsent,
    ReminderPreferences,
)
from .operational import dispatch_operational, enqueue, schedule_operational
from .phone_links import receive_link

pytestmark = pytest.mark.django_db(transaction=True)
BASE = "/api/v1/notifications/"


@pytest.fixture
def house(settings):
    settings.OPERATIONAL_EMAIL_ENABLED = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.OUTBOUND_EMAIL_ALLOWLIST = []
    settings.TEST_EMAIL_REDIRECT_TO = ""
    settings.SMS_ENABLED = False
    settings.WHATSAPP_ENABLED = False
    cache.clear()
    org = Organization.objects.create(name="Notification household")
    user = get_user_model()
    manager = user.objects.create_user(username="notice-manager", email="manager@example.com")
    tenant_user = user.objects.create_user(username="notice-tenant", email="tenant@example.com")
    for who, role in [(manager, "landlord"), (tenant_user, "tenant")]:
        OrganizationMembership.objects.create(organization=org, user=who, role=role)
    lease = make_lease(org)
    tenant = lease.tenant
    tenant.user, tenant.email = tenant_user, tenant_user.email
    tenant.save()
    invoice = create_invoice(
        organization=org,
        tenant=tenant,
        lease=lease,
        issue_date=timezone.localdate(),
        due_date=timezone.localdate(),
        lines=[{"kind": "rent", "description": "Rent", "amount": 100}],
    )
    OperationalDelivery.objects.all().delete()
    return org, manager, tenant_user, lease, invoice


def client(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def paid(house):
    return record_payment(
        invoice=house[4],
        amount=Decimal("50"),
        method="bank_transfer",
        paid_on=timezone.localdate(),
        recorded_by=None,
    )


def test_unattributed_payment_emails_both_sides_once(house, mailoutbox, settings):
    settings.MESSAGING_EMAIL_ENABLED = False
    for user in house[1:3]:
        NotificationPreferences.objects.create(user=user, email_enabled=False)
    payment = paid(house)
    enqueue(payment, "payment.confirmed")
    assert (
        OperationalDelivery.objects.filter(event="payment.confirmed", channel="email").count() == 2
    )
    assert dispatch_operational() == 2
    assert {m.to[0] for m in mailoutbox} == {"manager@example.com", "tenant@example.com"}
    assert all(payment.receipt_number in m.body for m in mailoutbox)
    assert dispatch_operational() == 0


def test_business_rollback_does_not_leave_notice_or_payment(house):
    with pytest.raises(ValueError), transaction.atomic():
        paid(house)
        raise ValueError("rollback")
    assert not Payment.objects.exists()
    assert not OperationalDelivery.objects.exists()


def test_correction_suppresses_unsent_confirmation(house, mailoutbox):
    payment = paid(house)
    reverse_payment(payment, reason="Duplicate entry", user=house[1])
    assert dispatch_operational() == 1
    assert all("Payment corrected" in m.subject for m in mailoutbox)
    assert OperationalDelivery.objects.filter(reason="event_superseded").count() == 2


@pytest.mark.parametrize("change", ["membership", "suspended", "contact", "tenant_reassigned"])
def test_removed_access_or_changed_contact_is_never_mailed(house, mailoutbox, change):
    org, manager, tenant_user, lease, _ = house
    paid(house)
    if change == "membership":
        OrganizationMembership.objects.filter(user=manager).update(is_active=False)
    elif change == "suspended":
        org.is_active = False
        org.save()
    elif change == "contact":
        manager.email = "changed@example.com"
        manager.save()
    else:
        lease.tenant.user = None
        lease.tenant.save()
    dispatch_operational()
    if change == "suspended":
        assert not mailoutbox
    elif change == "tenant_reassigned":
        assert [m.to for m in mailoutbox] == [[manager.email]]
    else:
        assert [m.to for m in mailoutbox] == [[tenant_user.email]]


def test_cross_workspace_target_cannot_leak(house, mailoutbox):
    paid(house)
    other = Organization.objects.create(name="Other household")
    OperationalDelivery.objects.update(organization=other)
    assert dispatch_operational() == 0
    assert not mailoutbox


def test_private_repair_comment_never_creates_mail(house, mailoutbox):
    org, manager, tenant_user, lease, _ = house
    job = create_request(
        organization=org,
        reported_by=tenant_user,
        tenant=lease.tenant,
        unit=lease.unit,
        property=lease.unit.property,
        title="Leaking tap",
    )
    OperationalDelivery.objects.all().delete()
    MaintenanceUpdate.objects.create(
        request=job, author=manager, body="Private pricing", is_internal=True
    )
    assert not OperationalDelivery.objects.exists()
    MaintenanceUpdate.objects.create(request=job, author=manager, body="Contractor coming")
    assert dispatch_operational() == 1
    assert all("Private pricing" not in m.body for m in mailoutbox)
    assert {m.to[0] for m in mailoutbox} == {tenant_user.email}


def test_repair_progress_and_invoice_have_email_events(house):
    org, _, tenant_user, lease, invoice = house
    enqueue(invoice, "invoice.issued")
    job = create_request(
        organization=org,
        reported_by=tenant_user,
        tenant=lease.tenant,
        unit=lease.unit,
        property=lease.unit.property,
        title="Broken lock",
    )
    start_request(job)
    assert set(OperationalDelivery.objects.values_list("event", flat=True)) == {
        "invoice.issued",
        "repair.created",
        "repair.status",
    }


def test_manager_comment_survives_notice_failure(house):
    org, manager, tenant_user, lease, _ = house
    job = create_request(
        organization=org,
        reported_by=tenant_user,
        tenant=lease.tenant,
        unit=lease.unit,
        property=lease.unit.property,
        title="Tap repair",
    )
    before = MaintenanceUpdate.objects.filter(request=job).count()
    with patch("apps.notifications.events.enqueue", side_effect=RuntimeError("outbox unavailable")):
        response = client(manager).post(
            f"/api/v1/maintenance/requests/{job.public_id}/updates/",
            {"body": "A public update"}, format="json",
        )
    assert response.status_code == 201
    assert MaintenanceUpdate.objects.filter(request=job).count() == before + 1


def test_known_quota_failure_waits_but_unknown_send_is_not_repeated(house, mailoutbox):
    paid(house)
    now = timezone.now()
    with patch(
        "apps.notifications.operational.EmailMessage.send", side_effect=EmailQuotaExceeded()
    ):
        assert dispatch_operational(now=now) == 0
    assert OperationalDelivery.objects.filter(reason="email_quota_reached").count() == 2
    with patch("apps.notifications.operational.EmailMessage.send", side_effect=TimeoutError()):
        assert dispatch_operational(now=now + timedelta(minutes=16)) == 0
    assert OperationalDelivery.objects.filter(status="review").count() == 2
    assert dispatch_operational(now=now + timedelta(hours=2)) == 0
    assert not mailoutbox


def test_unavailable_transport_retains_mandatory_email(house, mailoutbox):
    paid(house)
    with patch("apps.notifications.operational.delivery_configured", return_value=False):
        assert dispatch_operational() == 0
    assert OperationalDelivery.objects.filter(status="held").count() == 2
    assert not mailoutbox


def test_default_reminders_and_expiry_are_mandatory_and_deduplicated(house):
    org, manager, tenant_user, lease, invoice = house
    NotificationPreferences.objects.create(user=tenant_user, email_enabled=False)
    lease.end_date = timezone.localdate() + timedelta(days=30)
    lease.save(update_fields=["end_date"])
    now = timezone.localtime().replace(hour=12)
    schedule_operational(now=now)
    count = OperationalDelivery.objects.count()
    schedule_operational(now=now)
    assert OperationalDelivery.objects.count() == count
    assert (
        OperationalDelivery.objects.filter(event="invoice.reminder", channel="email").count() == 1
    )
    assert OperationalDelivery.objects.filter(event="lease.expiry", channel="email").count() == 2
    assert OperationalScan.objects.filter(completed=True).count() == 2


def test_listing_is_scoped_and_queries_do_not_grow_per_row(house):
    paid(house)
    api = client(house[1])
    with CaptureQueriesContext(connection) as small:
        response = api.get(BASE + "operational-messages/")
    small_count = len(small)
    assert response.status_code == 200
    for number in range(24):
        enqueue(house[4], "invoice.void", suffix=str(number))
    with CaptureQueriesContext(connection) as full:
        response = api.get(BASE + "operational-messages/")
    full_count = len(full)
    assert response.status_code == 200
    assert small_count > 0 and full_count <= small_count
    assert response["Cache-Control"] == "private, no-store"
    assert client(house[2]).get(BASE + "operational-messages/").status_code == 403
    assert APIClient().get(BASE + "operational-messages/").status_code in {401, 403}
    assert api.get(BASE + "platform-operational-messages/").status_code == 403
    stranger = get_user_model().objects.create_user(username="other-manager")
    org = Organization.objects.create(name="Empty portfolio")
    OrganizationMembership.objects.create(organization=org, user=stranger, role="landlord")
    empty = client(stranger).get(BASE + "operational-messages/").json()["response_data"]
    assert not empty
    print(f"Operational listing queries small={small_count}, full={full_count}")


def test_late_workspace_schedule_cannot_block_another_workspace(house):
    ReminderPreferences.objects.create(organization=house[0], due_hour=23)
    other = Organization.objects.create(name="Earlier schedule")
    lease = make_lease(other)
    lease.tenant.email = "earlier@example.com"
    lease.tenant.save(update_fields=["email"])
    invoice = create_invoice(
        organization=other,
        tenant=lease.tenant,
        lease=lease,
        issue_date=timezone.localdate(),
        due_date=timezone.localdate(),
        lines=[{"kind": "rent", "description": "Rent", "amount": 100}],
    )
    now = timezone.localtime().replace(hour=12)
    schedule_operational(limit=1, now=now)
    schedule_operational(limit=1, now=now)
    earlier = OperationalDelivery.objects.get(
        event="invoice.reminder",
        target_id=invoice.pk,
        channel="email",
    )
    later = OperationalDelivery.objects.get(
        event="invoice.reminder",
        target_id=house[4].pk,
        channel="email",
    )
    assert earlier.available_at <= now < later.available_at


def test_phone_pairing_requires_inbound_proof_and_account_side_completion(house, settings):
    settings.WHATSAPP_PUBLIC_NUMBER = "+260971000000"
    api = client(house[1])
    issued = api.post(
        BASE + "phone-link/",
        {
            "channel": "whatsapp",
            "phone": "+260971234567",
            "consent": True,
        },
        format="json",
    )
    assert issued.status_code == 200, issued.content
    data = issued.json()["response_data"]
    assert data["message"].split()[1] not in NotificationPhoneLink.objects.get().token_hash
    assert (
        api.post(
            BASE + "phone-link/", {"channel": "whatsapp", "complete": data["id"]}, format="json"
        ).status_code
        == 400
    )
    assert not receive_link("whatsapp", "+260979999999", data["message"], timezone.now())
    assert receive_link("whatsapp", "+260971234567", data["message"], timezone.now())
    assert not PhoneMessagingConsent.objects.exists()
    assert (
        client(house[2])
        .post(
            BASE + "phone-link/",
            {
                "channel": "whatsapp",
                "complete": data["id"],
            },
            format="json",
        )
        .status_code
        == 400
    )
    completed = api.post(
        BASE + "phone-link/", {"channel": "whatsapp", "complete": data["id"]}, format="json"
    )
    assert completed.status_code == 200
    assert PhoneMessagingConsent.objects.get().source == "verified_link"
    assert (
        api.post(
            BASE + "phone-link/", {"channel": "whatsapp", "complete": data["id"]}, format="json"
        ).status_code
        == 400
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"phone": "wrong", "channel": "whatsapp", "consent": True},
        {"phone": "+260971234567", "channel": "email", "consent": True},
        {"phone": "+260971234567", "channel": "sms", "consent": False},
        {"channel": "whatsapp", "complete": -1},
    ],
)
def test_invalid_pairing_inputs_do_not_grant_consent(house, payload):
    assert client(house[1]).post(BASE + "phone-link/", payload, format="json").status_code == 400
    assert not PhoneMessagingConsent.objects.exists()


def test_phone_pairing_expiry_throttle_and_authentication(house, settings):
    settings.WHATSAPP_PUBLIC_NUMBER = "+260971000000"
    data = {"channel": "whatsapp", "phone": "+260971234567", "consent": True}
    assert APIClient().post(BASE + "phone-link/", data).status_code in {401, 403}
    api = client(house[1])
    issued = api.post(BASE + "phone-link/", data, format="json").json()["response_data"]
    NotificationPhoneLink.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert not receive_link("whatsapp", data["phone"], issued["message"], timezone.now())
    for _ in range(4):
        assert api.post(BASE + "phone-link/", data, format="json").status_code == 200
    assert api.post(BASE + "phone-link/", data, format="json").status_code == 429


@pytest.mark.parametrize("channel", ["sms", "whatsapp"])
def test_verified_optional_manager_channel_sends_alongside_required_email(
    house,
    settings,
    mailoutbox,
    channel,
):
    NotificationPreferences.objects.create(user=house[1], **{f"{channel}_enabled": True})
    PhoneMessagingConsent.objects.create(
        user=house[1],
        channel=channel,
        phone="+260971234567",
        allowed=True,
        source="verified_link",
        granted_at=timezone.now(),
        last_inbound_at=timezone.now(),
    )
    paid(house)
    now = (timezone.now() + timedelta(days=1)).replace(hour=12)
    with (
        patch("apps.notifications.operational.phone_allowed", return_value=True),
        patch("apps.notifications.operational.sms_ready", return_value=True),
        patch("apps.notifications.operational.whatsapp_ready", return_value=True),
        patch("apps.notifications.operational.send_sms", return_value="sms-123") as sms,
        patch(
            "apps.notifications.operational.post_json",
            return_value={
                "messages": [{"id": "wa-123"}],
            },
        ) as whatsapp,
    ):
        assert dispatch_operational(now=now) == 3, list(
            OperationalDelivery.objects.values("channel", "status", "reason")
        )
    assert len(mailoutbox) == 2
    assert sms.call_count == (channel == "sms")
    assert whatsapp.call_count == (channel == "whatsapp")


def test_phone_opt_out_never_blocks_required_email(house, mailoutbox):
    NotificationPreferences.objects.create(user=house[1], whatsapp_enabled=True)
    PhoneMessagingConsent.objects.create(
        user=house[1],
        channel="whatsapp",
        phone="+260971234567",
        allowed=False,
        source="whatsapp_stop",
        granted_at=timezone.now(),
    )
    paid(house)
    with patch("apps.notifications.operational.post_json") as send:
        assert dispatch_operational() == 2
    send.assert_not_called()
    assert len(mailoutbox) == 2


def test_expired_service_window_requires_approved_operational_template(house, settings):
    settings.WHATSAPP_OPERATIONAL_TEMPLATE = ""
    NotificationPreferences.objects.create(user=house[1], whatsapp_enabled=True)
    PhoneMessagingConsent.objects.create(
        user=house[1],
        channel="whatsapp",
        phone="+260971234567",
        allowed=True,
        source="verified_link",
        granted_at=timezone.now(),
        last_inbound_at=timezone.now() - timedelta(days=2),
    )
    paid(house)
    with (
        patch("apps.notifications.operational.phone_allowed", return_value=True),
        patch("apps.notifications.operational.whatsapp_ready", return_value=True),
        patch("apps.notifications.operational.post_json") as send,
    ):
        assert dispatch_operational(now=(timezone.now() + timedelta(days=1)).replace(hour=12)) == 2
    send.assert_not_called()
    assert (
        OperationalDelivery.objects.filter(reason="operational_template_required").count() == 1
    ), list(OperationalDelivery.objects.values("channel", "status", "reason"))


def test_signed_inbound_connect_code_marks_only_intended_number(house, settings):
    from .test_phone_messaging import callback

    settings.WHATSAPP_PUBLIC_NUMBER = "+260971000000"
    settings.WHATSAPP_APP_SECRET = "test-app-secret"
    settings.WHATSAPP_PHONE_NUMBER_ID = "phone-id"
    settings.WHATSAPP_BUSINESS_ACCOUNT_ID = "business-id"
    data = (
        client(house[1])
        .post(
            BASE + "phone-link/",
            {
                "channel": "whatsapp",
                "phone": "+260971234567",
                "consent": True,
            },
            format="json",
        )
        .json()["response_data"]
    )
    event = {
        "messages": [
            {
                "id": "connect-1",
                "from": "260971234567",
                "type": "text",
                "timestamp": str(int(timezone.now().timestamp())),
                "text": {"body": data["message"]},
            }
        ]
    }
    assert callback(event, signature=False).status_code == 403
    assert NotificationPhoneLink.objects.get().verified_at is None
    assert callback(event).status_code == 200
    assert NotificationPhoneLink.objects.get().verified_at is not None
    assert not PhoneMessagingConsent.objects.filter(allowed=True).exists()


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL worker claim race")
def test_two_workers_cannot_send_the_same_email_twice(house):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import connections

    paid(house)
    barrier = Barrier(2)

    def work():
        connections.close_all()
        try:
            barrier.wait(timeout=10)
            return dispatch_operational()
        finally:
            connections.close_all()

    with patch("apps.notifications.operational.EmailMessage.send", return_value=1) as send:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sum(pool.map(lambda _: work(), range(2))) == 2
    assert send.call_count == 2


def test_email_pause_keeps_queue_and_resume_sends(house, settings, mailoutbox):
    paid(house)
    settings.OPERATIONAL_EMAIL_ENABLED = False
    assert dispatch_operational() == 0
    assert OperationalDelivery.objects.filter(status="queued", attempts=0).count() == 2
    assert not mailoutbox
    settings.OPERATIONAL_EMAIL_ENABLED = True
    assert dispatch_operational() == 2
    assert all(getattr(m, "dwella_bulk", False) for m in mailoutbox)
    assert all("@dwella.properties>" in m.extra_headers["Message-ID"] for m in mailoutbox)


def test_blank_email_skipped_and_old_email_expires_without_starving_new(house, mailoutbox):
    invoice = house[4]
    invoice.tenant.email = ""
    invoice.tenant.save(update_fields=["email"])
    enqueue(invoice, "invoice.issued")
    assert not OperationalDelivery.objects.exists()
    invoice.tenant.email = "tenant@example.com"
    invoice.tenant.save(update_fields=["email"])
    enqueue(invoice, "invoice.issued", suffix="old")
    OperationalDelivery.objects.update(created_at=timezone.now() - timedelta(days=8), status="held")
    enqueue(invoice, "invoice.issued", suffix="new")
    assert dispatch_operational(limit=1) == 1
    assert OperationalDelivery.objects.filter(reason="email_expired").count() == 1
    assert len(mailoutbox) == 1


def test_invoice_issued_tenant_only_and_manual_payment_excludes_actor(house):
    enqueue(house[4], "invoice.issued")
    assert list(OperationalDelivery.objects.values_list("audience", flat=True)) == ["tenant"]
    OperationalDelivery.objects.all().delete()
    record_payment(
        invoice=house[4], amount=Decimal("20"), method="cash",
        paid_on=timezone.localdate(), recorded_by=house[1],
    )
    assert list(OperationalDelivery.objects.values_list("recipient_user_id", flat=True)) == [
        house[2].pk,
    ]


def test_database_enqueue_failure_rolls_back_only_notice_savepoint(house, caplog):
    real_enqueue = enqueue

    def broken(*args, **kwargs):
        real_enqueue(*args, **kwargs)
        OperationalDelivery.objects.create(identity="invalid-row")

    with patch("apps.notifications.events.enqueue", side_effect=broken), transaction.atomic():
        payment = paid(house)
        assert Payment.objects.filter(pk=payment.pk).exists()
        assert not OperationalDelivery.objects.exists()
    assert Payment.objects.filter(pk=payment.pk).exists()
    assert "Operational notice enqueue failed" in caplog.text
    assert "IntegrityError" in caplog.text


def test_scheduled_for_only_save_emits_once(house):
    org, manager, _, lease, _ = house
    job = create_request(
        organization=org, reported_by=manager, tenant=lease.tenant,
        unit=lease.unit, property=lease.unit.property, title="Repair",
    )
    OperationalDelivery.objects.all().delete()
    job.scheduled_for = timezone.now() + timedelta(days=1)
    job.save(update_fields=["scheduled_for"])
    assert OperationalDelivery.objects.filter(event="repair.status").count() == 2
    job.save(update_fields=["scheduled_for"])
    assert OperationalDelivery.objects.count() == 2
    original = job.scheduled_for
    job.scheduled_for += timedelta(hours=1)
    job.save(update_fields=["scheduled_for"])
    job.scheduled_for = original
    job.save(update_fields=["scheduled_for"])
    assert OperationalDelivery.objects.filter(event="repair.status").count() == 6


@pytest.mark.parametrize("source", ["tenant_settings", "verified_link"])
def test_tenant_operational_phone_requires_verified_link(house, source):
    from .operational import send_phone

    tenant = house[3].tenant
    NotificationPreferences.objects.create(user=house[2], sms_enabled=True)
    PhoneMessagingConsent.objects.create(
        user=house[2], channel="sms", phone=tenant.phone_number, allowed=True,
        source=source, granted_at=timezone.now(),
    )
    enqueue(house[4], "invoice.issued")
    row = OperationalDelivery.objects.select_related("tenant", "organization").get(channel="sms")
    with (
        patch("apps.notifications.operational.phone_allowed", return_value=True),
        patch("apps.notifications.operational.sms_ready", return_value=True),
        patch("apps.notifications.operational.send_sms", return_value="sms-ok") as send,
    ):
        status, reason, _ = send_phone(
            row, "Invoice", "Body", "https://example.com", timezone.localtime().replace(hour=12),
        )
    if source == "verified_link":
        assert status == "sent"
        send.assert_called_once()
    else:
        assert (status, reason) == ("held", "verified_phone_required")
        send.assert_not_called()


def test_tenant_delete_does_not_fail_or_send_orphaned_notice(house, mailoutbox):
    from apps.tenants.models import Tenant

    tenant = Tenant.objects.create(
        organization=house[0], full_name="Removable Tenant", phone_number="+260971000099",
        email="old@example.com",
    )
    row = OperationalDelivery.objects.create(
        organization=house[0], tenant=tenant, audience="tenant", channel="email",
        identity="orphan-test", event="invoice.issued", target_model="billing.invoice",
        target_id=house[4].pk, recipient="old@example.com",
    )
    tenant.delete()
    row.refresh_from_db()
    assert row.tenant_id is None
    assert dispatch_operational() == 0
    row.refresh_from_db()
    assert row.reason == "permission_removed"
    assert not mailoutbox


def test_local_day_scan_does_not_reset_at_utc_midnight(house):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    org, _, _, _, invoice = house
    org.timezone = "America/Los_Angeles"
    org.save(update_fields=["timezone"])
    before = datetime(2026, 11, 2, 23, 50, tzinfo=ZoneInfo("UTC"))
    invoice.due_date = before.astimezone(ZoneInfo(org.timezone)).date()
    invoice.save(update_fields=["due_date"])
    schedule_operational(now=before)
    count = OperationalDelivery.objects.filter(event="invoice.reminder").count()
    assert count == 1
    schedule_operational(now=before + timedelta(minutes=20))
    scan = OperationalScan.objects.get(source="invoices:America/Los_Angeles")
    assert scan.day == invoice.due_date
    assert OperationalDelivery.objects.filter(event="invoice.reminder").count() == count
    schedule_operational(now=before + timedelta(hours=9))
    scan.refresh_from_db()
    assert scan.day == invoice.due_date + timedelta(days=1)


def test_cleanup_bounds_old_held_and_review_rows(house):
    from django.core.management import call_command

    paid(house)
    OperationalDelivery.objects.update(
        status="review", created_at=timezone.now() - timedelta(days=91),
    )
    with (
        patch("apps.notifications.management.commands.run_operational_messages.schedule_operational"),
        patch("apps.notifications.management.commands.run_operational_messages.dispatch_operational"),
    ):
        call_command("run_operational_messages")
    assert not OperationalDelivery.objects.exists()


def test_deleted_account_cannot_become_accountless_email(house, mailoutbox):
    paid(house)
    house[2].delete()
    tenant_row = OperationalDelivery.objects.get(audience="tenant")
    assert tenant_row.recipient_user_id is None
    assert tenant_row.status == "cancelled"
    assert dispatch_operational() == 1
    assert [m.to for m in mailoutbox] == [[house[1].email]]


def test_sms_pairing_short_code_proves_same_phone_and_preserves_verification(house, settings):
    from .phone_messaging import save_user_consent
    from .test_sms_messaging import TOKEN, callback

    settings.SMS_INCOMING_NUMBER = "12345"
    settings.AFRICASTALKING_CALLBACK_TOKEN = TOKEN
    tenant = house[3].tenant
    api = client(house[2])
    response = api.post(
        BASE + "phone-link/",
        {"channel": "sms", "phone": tenant.phone_number, "consent": True}, format="json",
    )
    assert response.status_code == 200
    data = response.json()["response_data"]
    assert len(data["message"].split()[1]) == 8
    assert data["destination"] == "12345"
    assert callback(
        "incoming", {"from": tenant.phone_number, "to": "12345", "text": data["message"]},
    ).status_code == 200
    assert api.post(
        BASE + "phone-link/", {"channel": "sms", "complete": data["id"]}, format="json",
    ).status_code == 200
    save_user_consent(house[2], {"sms_enabled": True})
    consent = PhoneMessagingConsent.objects.get(channel="sms", phone=tenant.phone_number)
    assert consent.allowed and consent.source == "verified_link"


def test_request_actor_is_excluded_and_context_is_cleared(house):
    from .actor_context import current_actor

    lease = house[3]
    response = client(house[1]).post(f"/api/v1/leases/{lease.public_id}/end/")
    assert response.status_code == 200, response.content
    assert list(OperationalDelivery.objects.filter(event="lease.ended").values_list(
        "audience", flat=True,
    )) == ["tenant"]
    assert current_actor() is None
