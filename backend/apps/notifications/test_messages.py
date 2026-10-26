# ruff: noqa: F811
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import EmailMessage, get_connection
from django.db import connection
from django.db.models import Q
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.assistant.test_actions import JWT_SETTINGS
from apps.assistant.test_actions import client_for as handy_client
from apps.billing.models import Invoice
from apps.organizations.models import Organization, OrganizationMembership
from apps.payments.testing import client_for, home  # noqa: F401
from apps.tenants.models import Tenant

from .messaging import dispatch_messages, schedule_reminders
from .models import (
    MessageDelivery,
    MessageRequest,
    MessagingSettings,
    NotificationPreferences,
    ReminderPreferences,
)

pytestmark = pytest.mark.django_db
BASE = "/api/v1/notifications/"


@pytest.fixture(autouse=True)
def reset_cache():
    cache.clear()


def compose_data(home, channel="email"):
    tenant = home["invoice"].tenant
    tenant.email = "tenant@example.com"
    tenant.save(update_fields=["email"])
    return {
        "channel": channel,
        "tenants": [str(tenant.public_id)],
        "subject": "Water notice",
        "body": "Water supply maintenance tomorrow.",
    }


def make_preview(home, channel="email"):
    response = client_for(home["manager"]).post(
        BASE + "message-previews/", compose_data(home, channel), format="json"
    )
    assert response.status_code == 201, response.content
    return response.json()["response_data"]


def confirm_preview(home, value):
    return client_for(home["manager"]).post(
        BASE + f"message-previews/{value['id']}/confirm/", {"confirmed": True}, format="json"
    )


@pytest.mark.parametrize("path", ["messages/", "message-recipients/", "platform-messages/"])
def test_lists_require_authentication(path):
    assert APIClient().get(BASE + path).status_code in {401, 403}


@pytest.mark.parametrize("channel", ["email", "sms", "whatsapp"])
def test_preview_confirm_once_unconnected_is_held(home, channel, mailoutbox):
    value = make_preview(home, channel)
    assert not MessageDelivery.objects.exists()
    assert confirm_preview(home, value).status_code == 200
    assert confirm_preview(home, value).status_code == 200
    row = MessageDelivery.objects.get()
    assert row.status == "held" and row.reason == "delivery_not_connected"
    assert dispatch_messages() == 0 and not mailoutbox


@pytest.mark.parametrize(
    "bad",
    [
        {"channel": "fax"},
        {"tenants": []},
        {"tenants": ["bad"]},
        {"body": ""},
        {"body": "x" * 2001},
        {"subject": "bad\r\nBcc: other@example.com"},
        {"recipient": "external@example.com"},
    ],
)
def test_malformed_notice_rejected(home, bad):
    body = {**compose_data(home), **bad}
    assert (
        client_for(home["manager"])
        .post(BASE + "message-previews/", body, format="json")
        .status_code
        == 400
    )
    assert not MessageRequest.objects.exists()


def test_tenant_foreign_workspace_and_suspension(home):
    body = compose_data(home)
    assert (
        client_for(home["tenant"]).post(BASE + "message-previews/", body, format="json").status_code
        == 403
    )
    foreign = Organization.objects.create(name="Foreign messages")
    target = Tenant.objects.create(
        organization=foreign,
        full_name="Private",
        phone_number="+260970000999",
        email="private@example.com",
    )
    body["tenants"] = [str(target.public_id)]
    assert (
        client_for(home["manager"])
        .post(BASE + "message-previews/", body, format="json")
        .status_code
        == 400
    )
    home["org"].is_active = False
    home["org"].save()
    assert client_for(home["manager"]).get(BASE + "messages/").status_code == 403


def test_expired_changed_and_unconfirmed_preview(home):
    value = make_preview(home)
    url = BASE + f"message-previews/{value['id']}/confirm/"
    client = client_for(home["manager"])
    assert client.post(url, {"confirmed": False}, format="json").status_code == 400
    assert (
        client.post(url, {"confirmed": True, "body": "Changed"}, format="json").status_code == 400
    )
    tenant = home["invoice"].tenant
    tenant.email = "changed@example.com"
    tenant.save()
    assert confirm_preview(home, value).status_code == 400
    MessageRequest.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert confirm_preview(home, value).status_code == 400
    assert not MessageDelivery.objects.exists()


def test_other_manager_cannot_confirm_preview(home):
    value = make_preview(home)
    user = get_user_model().objects.create_user(username="second-manager")
    OrganizationMembership.objects.create(organization=home["org"], user=user, role="landlord")
    assert (
        client_for(user)
        .post(BASE + f"message-previews/{value['id']}/confirm/", {"confirmed": True}, format="json")
        .status_code
        == 404
    )


def test_throttled_preview(home):
    from .message_views import MessageWriteThrottle

    with patch.object(MessageWriteThrottle, "rate", "1/hour"):
        body = compose_data(home)
        client = client_for(home["manager"])
        assert client.post(BASE + "message-previews/", body, format="json").status_code == 201
        assert client.post(BASE + "message-previews/", body, format="json").status_code == 429


def enable_email(settings):
    settings.MESSAGING_EMAIL_ENABLED = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def due_today(home, now):
    invoice = home["invoice"]
    invoice.due_date = now.date()
    invoice.tenant.email = "rent@example.com"
    invoice.tenant.save()
    invoice.save()
    return invoice


def test_scheduler_runs_once_a_day_and_stops_paid_invoices(home, settings):
    enable_email(settings)
    now = timezone.now().replace(hour=12)
    invoice = due_today(home, now)
    pref = ReminderPreferences.objects.create(
        organization=home["org"], email_enabled=True, sms_enabled=True, whatsapp_enabled=True
    )
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    # SMS and WhatsApp are not connected, so only email is scheduled.
    assert schedule_reminders(now=now) == 1
    assert schedule_reminders(now=now) == 0
    assert MessageDelivery.objects.get().channel == "email"
    MessageDelivery.objects.all().delete()
    ReminderPreferences.objects.filter(pk=pref.pk).update(run_date=None, next_run_at=None)
    invoice.status = "paid"
    invoice.amount_paid = invoice.total
    invoice.save()
    assert schedule_reminders(now=now) == 0


def test_unconnected_channels_schedule_nothing(home):
    now = timezone.now().replace(hour=12)
    due_today(home, now)
    ReminderPreferences.objects.create(
        organization=home["org"], email_enabled=True, sms_enabled=True, whatsapp_enabled=True
    )
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    assert schedule_reminders(now=now) == 0
    assert not MessageDelivery.objects.exists()


def test_scheduler_waits_for_the_workspace_reminder_hour(home, settings):
    enable_email(settings)
    now = timezone.now().replace(hour=12)
    due_today(home, now)
    ReminderPreferences.objects.create(organization=home["org"], email_enabled=True, due_hour=23)
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    assert schedule_reminders(now=now) == 0
    assert ReminderPreferences.objects.get().run_date is None


@pytest.mark.parametrize("days,expected", [(-3, 1), (-2, 0), (0, 1), (3, 1), (9, 1), (12, 0)])
def test_before_due_and_overdue_schedule(home, settings, days, expected):
    enable_email(settings)
    now = timezone.now().replace(hour=12)
    invoice = home["invoice"]
    invoice.due_date = now.date() - timedelta(days=days)
    invoice.tenant.email = "rent@example.com"
    invoice.tenant.save()
    invoice.save()
    ReminderPreferences.objects.create(organization=home["org"], email_enabled=True)
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    assert schedule_reminders(now=now) == expected


def queued_email(home, settings):
    settings.MESSAGING_EMAIL_ENABLED = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    value = make_preview(home)
    assert confirm_preview(home, value).status_code == 200
    return MessageDelivery.objects.get()


def test_dispatch_once_and_no_smtp_inside_transaction(home, settings, mailoutbox):
    row = queued_email(home, settings)
    now = timezone.now().replace(hour=12)
    row.available_at = now - timedelta(seconds=1)
    row.save()
    assert dispatch_messages(now=now) == 1
    assert dispatch_messages(now=now) == 0
    assert len(mailoutbox) == 1
    row.refresh_from_db()
    assert row.status == "sent" and row.reason == "smtp_accepted"


@pytest.mark.parametrize(
    "change,reason",
    [
        ("membership", "permission_removed"),
        ("contact", "recipient_changed"),
        ("workspace", "permission_removed"),
    ],
)
def test_dispatch_rechecks_authority(home, settings, mailoutbox, change, reason):
    row = queued_email(home, settings)
    if change == "membership":
        OrganizationMembership.objects.filter(user=home["manager"]).update(is_active=False)
    elif change == "contact":
        Tenant.objects.filter(pk=row.tenant_id).update(email="changed@example.com")
    else:
        Organization.objects.filter(pk=home["org"].pk).update(is_active=False)
    dispatch_messages(now=timezone.now().replace(hour=12) + timedelta(days=1))
    row.refresh_from_db()
    assert row.reason == reason and not mailoutbox


def test_uncertain_send_never_retries(home, settings):
    row = queued_email(home, settings)
    with patch("apps.notifications.messaging.EmailMessage.send", side_effect=TimeoutError) as send:
        dispatch_messages(now=timezone.now().replace(hour=12) + timedelta(days=1))
        dispatch_messages(now=timezone.now().replace(hour=12) + timedelta(days=1))
    row.refresh_from_db()
    assert row.status == "review" and send.call_count == 1


def test_enabling_delivery_does_not_release_old_holds(home, settings, mailoutbox):
    confirm_preview(home, make_preview(home))
    settings.MESSAGING_EMAIL_ENABLED = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    assert dispatch_messages() == 0 and not mailoutbox


def test_recipient_opt_out_is_respected(home, settings, mailoutbox):
    row = queued_email(home, settings)
    NotificationPreferences.objects.create(user=home["tenant"], email_enabled=False)
    dispatch_messages(now=timezone.now().replace(hour=12) + timedelta(days=1))
    row.refresh_from_db()
    assert row.status == "held" and row.reason == "recipient_opted_out"
    assert not mailoutbox


def test_quiet_hours_defer_without_starving_other_requests(home, settings, mailoutbox):
    row = queued_email(home, settings)
    now = timezone.now().replace(hour=22) + timedelta(days=1)
    assert dispatch_messages(now=now) == 0
    row.refresh_from_db()
    assert row.status == "queued" and row.available_at > now
    assert dispatch_messages(now=row.available_at + timedelta(minutes=1)) == 1
    assert len(mailoutbox) == 1


@pytest.mark.parametrize("late_days,status", [(1, "sent"), (2, "cancelled")])
def test_reminder_may_go_one_day_late(home, settings, mailoutbox, late_days, status):
    enable_email(settings)
    now = timezone.now().replace(hour=12)
    due_today(home, now)
    ReminderPreferences.objects.create(organization=home["org"], email_enabled=True)
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    assert schedule_reminders(now=now) == 1
    dispatch_messages(now=now + timedelta(days=late_days))
    assert MessageDelivery.objects.get().status == status


def test_reminder_paid_between_schedule_and_send_is_cancelled(home, settings, mailoutbox):
    settings.MESSAGING_EMAIL_ENABLED = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    now = timezone.now().replace(hour=12) + timedelta(days=1)
    invoice = home["invoice"]
    invoice.due_date = now.date()
    invoice.tenant.email = "rent@example.com"
    invoice.tenant.save()
    invoice.save()
    ReminderPreferences.objects.create(organization=home["org"], email_enabled=True)
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    assert schedule_reminders(now=now) == 1
    invoice.status, invoice.amount_paid = "paid", invoice.total
    invoice.save()
    dispatch_messages(now=now + timedelta(minutes=1))
    row = MessageDelivery.objects.get()
    assert row.status == "cancelled" and row.reason == "invoice_no_longer_due"
    assert not mailoutbox


def queue_emails(home, settings, count):
    enable_email(settings)
    start = Tenant.objects.count()
    tenants = [
        Tenant.objects.create(
            organization=home["org"],
            full_name=f"Notice {i}",
            phone_number=f"+26097555{i:04}",
            email=f"notice{i}@example.com",
        )
        for i in range(start, start + count)
    ]
    body = {**compose_data(home), "tenants": [str(t.public_id) for t in tenants]}
    value = client_for(home["manager"]).post(BASE + "message-previews/", body, format="json")
    assert confirm_preview(home, value.json()["response_data"]).status_code == 200


def test_daily_email_limit_leaves_the_rest_queued(home, settings, mailoutbox):
    queue_emails(home, settings, 3)
    settings.MESSAGING_EMAIL_DAILY_LIMIT = 2
    now = timezone.now().replace(hour=12) + timedelta(days=1)
    assert dispatch_messages(now=now) == 2
    assert dispatch_messages(now=now) == 0
    assert MessageDelivery.objects.filter(status="queued").count() == 1
    assert dispatch_messages(now=now + timedelta(hours=25)) == 1


def test_one_mail_connection_and_bounded_queries_per_batch(home, settings, mailoutbox):
    queue_emails(home, settings, 2)
    now = timezone.now().replace(hour=12) + timedelta(days=1)
    with patch("apps.notifications.messaging.get_connection", wraps=get_connection) as opened:
        with CaptureQueriesContext(connection) as two:
            assert dispatch_messages(now=now) == 2
    assert opened.call_count == 1
    MessageDelivery.objects.all().delete()
    queue_emails(home, settings, 6)
    with CaptureQueriesContext(connection) as six:
        assert dispatch_messages(now=now) == 6
    # Authority is re-checked for every message, so cost grows by a fixed amount per message.
    assert len(six) - len(two) <= 4 * 12


def test_failed_mail_connection_claims_nothing(home, settings):
    queue_emails(home, settings, 2)
    now = timezone.now().replace(hour=12) + timedelta(days=1)
    with patch("django.core.mail.backends.locmem.EmailBackend.open", side_effect=OSError):
        assert dispatch_messages(now=now) == 0
    assert MessageDelivery.objects.filter(status="queued").count() == 2


def test_notice_to_all_tenants_reports_who_is_left_out(home):
    Tenant.objects.create(organization=home["org"], full_name="No email", phone_number="+260970001")
    body = {**compose_data(home), "tenants": [], "all_tenants": True}
    client = client_for(home["manager"])
    response = client.post(BASE + "message-previews/", body, format="json")
    assert response.status_code == 201, response.content
    value = response.json()["response_data"]
    assert len(value["recipients"]) == 1 and value["skipped"] == 1
    both = {**compose_data(home), "all_tenants": True}
    neither = {**compose_data(home), "tenants": []}
    for bad in [both, neither]:
        assert client.post(BASE + "message-previews/", bad, format="json").status_code == 400


def test_reading_message_detail_is_not_throttled(home):
    from .message_views import MessageWriteThrottle

    confirm_preview(home, make_preview(home))
    row = MessageDelivery.objects.get()
    client = client_for(home["manager"])
    with patch.object(MessageWriteThrottle, "rate", "1/hour"):
        for _ in range(3):
            assert client.get(BASE + f"messages/{row.public_id}/").status_code == 200


def test_scheduling_is_bounded_and_resumes(home, settings):
    from apps.billing.services import generate_rent_invoices
    from apps.billing.tests import THIS_MONTH, make_lease

    enable_email(settings)
    for unit, phone in [("3B", "+260974123382"), ("4C", "+260974123383")]:
        make_lease(home["org"], unit_name=unit, phone=phone)
    generate_rent_invoices(home["org"], THIS_MONTH)
    now = timezone.now().replace(hour=12)
    invoices = Invoice.objects.filter(organization=home["org"])
    assert invoices.count() == 3
    invoices.update(due_date=now.date())
    Tenant.objects.filter(organization=home["org"]).update(email="rent@example.com")
    ReminderPreferences.objects.create(organization=home["org"], email_enabled=True)
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    # A limit of 3 covers the workspace itself plus two invoices.
    assert schedule_reminders(now=now, limit=3) == 2
    assert ReminderPreferences.objects.get().run_after_id is not None
    assert schedule_reminders(now=now, limit=3) == 1
    assert ReminderPreferences.objects.get().run_after_id is None
    assert schedule_reminders(now=now, limit=3) == 0
    assert MessageDelivery.objects.count() == 3


def test_scheduler_pages_workspaces_and_skips_finished_ones(home, settings):
    enable_email(settings)
    now = timezone.now().replace(hour=12)
    # No invoices fall due, so each workspace costs one unit of the limit.
    Invoice.objects.update(due_date=now.date() + timedelta(days=60))
    ReminderPreferences.objects.create(organization=home["org"], email_enabled=True)
    for i in range(5):
        org = Organization.objects.create(name=f"Reminder workspace {i}")
        ReminderPreferences.objects.create(organization=org, email_enabled=True)
    MessagingSettings.objects.create(pk=1, reminders_enabled=True)
    waiting = ReminderPreferences.objects.filter(
        Q(next_run_at__isnull=True) | Q(next_run_at__lte=now)
    )
    for remaining in [4, 2, 0]:
        schedule_reminders(now=now, limit=2)
        assert waiting.count() == remaining
    # Finished workspaces are not loaded: one empty query whatever their number.
    with CaptureQueriesContext(connection) as queries:
        assert schedule_reminders(now=now, limit=2) == 0
    loads = [q for q in queries if "notifications_reminderpreferences" in q["sql"]]
    assert len(loads) == 1
    assert schedule_reminders(now=now + timedelta(days=1), limit=10) == 0
    assert (
        ReminderPreferences.objects.filter(run_date=(now + timedelta(days=1)).date()).count() == 6
    )


def test_changing_the_schedule_recalculates_the_next_run(home):
    pref = ReminderPreferences.objects.create(
        organization=home["org"], email_enabled=True, next_run_at=timezone.now()
    )
    client = client_for(home["manager"])
    assert client.patch(BASE + "reminders/", {"due_hour": 15}, format="json").status_code == 200
    pref.refresh_from_db()
    assert pref.next_run_at is None


def test_revoked_access_stops_the_rest_of_the_batch(home, settings, mailoutbox):
    queue_emails(home, settings, 2)
    now = timezone.now().replace(hour=12) + timedelta(days=1)
    real_send = EmailMessage.send

    def send_then_revoke(message, *args, **kwargs):
        sent = real_send(message, *args, **kwargs)
        OrganizationMembership.objects.filter(user=home["manager"]).update(is_active=False)
        return sent

    with patch.object(EmailMessage, "send", send_then_revoke):
        assert dispatch_messages(now=now) == 1
    assert len(mailoutbox) == 1
    assert MessageDelivery.objects.filter(reason="permission_removed").count() == 1


def test_allowance_is_rechecked_when_claiming(home, settings, mailoutbox):
    queue_emails(home, settings, 2)
    settings.MESSAGING_EMAIL_DAILY_LIMIT = 1
    now = timezone.now().replace(hour=12) + timedelta(days=1)
    from . import messaging

    real_block = messaging.dispatch_block

    def other_worker_sends_first(row, *args):
        # Another run claims the other message after this run sized its batch.
        MessageDelivery.objects.exclude(pk=row.pk).update(status="sent", claimed_at=now)
        return real_block(row, *args)

    with patch.object(messaging, "dispatch_block", other_worker_sends_first):
        assert dispatch_messages(now=now) == 0
    assert not mailoutbox
    assert MessageDelivery.objects.filter(status="queued").count() == 1


def test_tenant_without_saved_preferences_gets_the_displayed_defaults(home, settings):
    shown = client_for(home["tenant"]).get(BASE + "preferences/").json()["response_data"]
    from .messaging import tenant_accepts

    for channel in ["email", "sms", "whatsapp"]:
        assert tenant_accepts(home["tenant"], channel) == shown["preferences"][f"{channel}_enabled"]
    client_for(home["tenant"]).patch(BASE + "preferences/", {"email_enabled": False}, format="json")
    home["tenant"].refresh_from_db()
    assert not tenant_accepts(home["tenant"], "email")


def test_foreign_history_and_detail_are_hidden(home):
    confirm_preview(home, make_preview(home))
    row = MessageDelivery.objects.get()
    user = get_user_model().objects.create_user(username="foreign-manager")
    org = Organization.objects.create(name="Other company messages")
    OrganizationMembership.objects.create(organization=org, user=user, role="landlord")
    client = client_for(user)
    assert client.get(BASE + "messages/").json()["response_data"] == []
    assert client.get(BASE + f"messages/{row.public_id}/").status_code == 404
    assert (
        client.post(
            BASE + f"messages/{row.public_id}/", {"confirmed": True}, format="json"
        ).status_code
        == 404
    )
    assert client.get(BASE + "platform-messages/").status_code == 403


@pytest.mark.django_db(transaction=True)
def test_real_dispatch_boundary_has_no_database_transaction(home, settings):
    queued_email(home, settings)

    def send(*args, **kwargs):
        assert not connection.in_atomic_block
        return 1

    with patch("apps.notifications.messaging.EmailMessage.send", side_effect=send):
        assert dispatch_messages(now=timezone.now().replace(hour=12) + timedelta(days=1)) == 1


def test_history_and_preview_query_counts_are_bounded(home):
    body = compose_data(home)
    client = client_for(home["manager"])
    with CaptureQueriesContext(connection) as small:
        assert client.post(BASE + "message-previews/", body, format="json").status_code == 201
    tenants = [
        Tenant.objects.create(
            organization=home["org"],
            full_name=f"Tenant {i}",
            phone_number=f"+26097123{i:04}",
            email=f"tenant{i}@example.com",
        )
        for i in range(25)
    ]
    body["tenants"] = [str(t.public_id) for t in tenants]
    with CaptureQueriesContext(connection) as full:
        response = client.post(BASE + "message-previews/", body, format="json")
        assert response.status_code == 201
    assert len(full) <= len(small) + 1
    confirm_preview(home, response.json()["response_data"])
    with CaptureQueriesContext(connection) as small:
        assert client.get(BASE + "messages/?page_size=1").status_code == 200
    with CaptureQueriesContext(connection) as full:
        assert client.get(BASE + "messages/?page_size=25").status_code == 200
    assert len(full) == len(small)


@JWT_SETTINGS
def test_handy_preview_and_explicit_confirm(home):
    from apps.audit.models import PlatformSettings

    PlatformSettings.objects.update_or_create(pk=1, defaults={"handy_agent_enabled": True})
    client = handy_client(home["manager"], home["org"])
    response = client.post("/api/v1/assistant/message-previews/", compose_data(home), format="json")
    assert response.status_code == 201, response.content
    value = response.json()["response_data"]
    assert not MessageDelivery.objects.exists()
    url = f"/api/v1/assistant/message-previews/{value['id']}/confirm/"
    assert client.post(url, {"confirmed": False}, format="json").status_code == 400
    assert client.post(url, {"confirmed": True}, format="json").status_code == 201
    assert client.post(url, {"confirmed": True}, format="json").status_code == 201
    assert MessageDelivery.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_postgres_competing_confirmation_creates_one_delivery(home):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks")
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections

    from .messaging import confirm

    value = make_preview(home)
    message = MessageRequest.objects.get(public_id=value["id"])
    barrier = Barrier(2)

    def run():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            confirm(message=message, actor=home["manager"])
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run) for _ in range(2)]
        for future in futures:
            future.result(timeout=20)
    assert MessageDelivery.objects.count() == 1


def test_postgres_message_tables_default_deny_external_readers():
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row security")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relname, relrowsecurity FROM pg_class WHERE relname IN (%s, %s)",
            ["notifications_messagerequest", "notifications_messagedelivery"],
        )
        rows = cursor.fetchall()
    assert len(rows) == 2 and all(row[1] for row in rows)
