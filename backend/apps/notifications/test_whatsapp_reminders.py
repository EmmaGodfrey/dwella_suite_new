"""Requested documents, confirmed repair photos and one-invoice reminder journeys."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.billing.models import Invoice
from apps.billing.tests import make_lease
from apps.notifications.messaging import dispatch_messages
from apps.organizations.models import Organization, OrganizationMembership

from . import test_whatsapp as base
from .models import (
    MessageDelivery,
    MessageRequest,
    MessagingSettings,
    NotificationPreferences,
    PhoneMessagingConsent,
)
from .test_whatsapp import PHONE, choose, step, workspace
from .whatsapp.access import actor_context, revoke
from .whatsapp.models import WhatsAppBinding, WhatsAppConversation

pytestmark = pytest.mark.django_db(transaction=True)
config = base.config
house = base.house


def reminder_preview(house, settings):
    settings.WHATSAPP_RENT_TEMPLATE = "dwella_rent_reminder"
    settings.OUTBOUND_PHONE_ALLOWLIST = [PHONE, "+260971234568"]
    tenant = house["lease"].tenant
    tenant.phone_number = "+260971234568"
    tenant.save()
    NotificationPreferences.objects.create(user=house["tenant"], whatsapp_enabled=True)
    PhoneMessagingConsent.objects.create(
        user=house["tenant"],
        channel="whatsapp",
        phone=tenant.phone_number,
        source="verified_link",
        allowed=True,
        granted_at=timezone.now(),
    )
    MessagingSettings.objects.update_or_create(
        pk=1,
        defaults={
            "reminders_enabled": True,
            "quiet_from": "23:58",
            "quiet_until": "00:01",
        },
    )
    menu = workspace(house, "manager")
    reply = step(token=choose(menu, "Send rent reminder"))
    return step(token=reply.view["options"][0]["id"])


def send_reminders():
    with (
        patch(
            "apps.notifications.phone_messaging.approved_whatsapp_templates",
            return_value={"dwella_rent_reminder:en"},
        ),
        patch(
            "apps.notifications.phone_messaging.post_json",
            return_value={"messages": [{"id": "wamid.reminder"}]},
        ) as send,
    ):
        dispatch_messages(now=timezone.now().replace(hour=12))
    return send


def test_manager_reminder_requires_confirmation_and_deduplicates_same_day(house, settings):
    reply = reminder_preview(house, settings)
    assert house["invoice"].reference in reply.view["text"] and not MessageDelivery.objects.exists()
    token = choose(reply, "Queue reminder")
    result = step(token=token)
    assert "Reminder queued" in result.view["text"] and MessageDelivery.objects.count() == 1
    step(token=token)
    menu = step("reminders")
    reply = step(token=menu.view["options"][0]["id"])
    step(token=choose(reply, "Queue reminder"))
    assert MessageDelivery.objects.count() == 1 and MessageRequest.objects.count() == 1
    send = send_reminders()
    assert send.call_count == 1
    assert send.call_args.args[1]["template"]["name"] == "dwella_rent_reminder"
    assert send.call_args.args[1]["to"] == "260971234568"


@pytest.mark.parametrize(
    "change",
    ["paid", "phone", "stop", "membership", "reconnect", "pause", "malformed", "tenant_account"],
)
def test_delayed_reminder_rechecks_recipient_money_actor_and_kill_switch(house, settings, change):
    reply = reminder_preview(house, settings)
    step(token=choose(reply, "Queue reminder"))
    if change == "paid":
        Invoice.objects.filter(pk=house["invoice"].pk).update(
            status="paid", amount_paid=house["invoice"].total
        )
    elif change == "phone":
        type(house["lease"].tenant).objects.update(phone_number="+260971234569")
    elif change == "stop":
        PhoneMessagingConsent.objects.filter(user=house["tenant"]).update(allowed=False)
    elif change == "membership":
        OrganizationMembership.objects.filter(user=house["manager"]).update(is_active=False)
    elif change == "reconnect":
        revoke(phone=PHONE)
    elif change == "malformed":
        MessageRequest.objects.update(
            recipients=[{"binding_id": 1, "binding_generation": "invalid"}]
        )
    elif change == "tenant_account":
        type(house["tenant"]).objects.filter(pk=house["tenant"].pk).update(is_active=False)
    else:
        MessagingSettings.objects.update(reminders_enabled=False)
    assert send_reminders().call_count == 0


def test_changed_reminder_preview_requires_a_new_confirmation(house, settings):
    reply = reminder_preview(house, settings)
    Invoice.objects.filter(pk=house["invoice"].pk).update(amount_paid=Decimal("100"))
    reply = step(token=choose(reply, "Queue reminder"))
    assert not MessageDelivery.objects.exists() and "Queue reminder" in str(reply.view["options"])
    step(token=choose(reply, "Queue reminder"))
    assert MessageDelivery.objects.count() == 1


def test_tenant_cannot_queue_manager_reminders(house):
    workspace(house)
    step("reminders")
    assert not MessageDelivery.objects.exists() and not MessageRequest.objects.exists()


def test_partial_payment_after_queue_restates_template_balance(house, settings):
    reply = reminder_preview(house, settings)
    step(token=choose(reply, "Queue reminder"))
    Invoice.objects.filter(pk=house["invoice"].pk).update(
        status="partially_paid",
        amount_paid=Decimal("100"),
    )
    send = send_reminders()
    assert send.call_count == 1
    parameters = send.call_args.args[1]["template"]["components"][0]["parameters"]
    assert parameters[3]["text"] == "ZMW 3800.00"


def test_reminder_rechecks_initiator_after_claim(house, settings):
    from .messaging import claim

    reply = reminder_preview(house, settings)
    step(token=choose(reply, "Queue reminder"))

    def changed(*args):
        claimed = claim(*args)
        revoke(phone=PHONE)
        return claimed

    with patch("apps.notifications.messaging.claim", side_effect=changed):
        assert send_reminders().call_count == 0
    assert MessageDelivery.objects.get().status == "cancelled"


def test_existing_scheduled_reminder_prevents_requested_duplicate(house, settings):
    from apps.reports.common import organization_today

    from .whatsapp.reminders import identity

    reply = reminder_preview(house, settings)
    MessageDelivery.objects.create(
        organization=house["org"],
        tenant=house["lease"].tenant,
        invoice=house["invoice"],
        channel="whatsapp",
        recipient="+260971234568",
        subject="Scheduled reminder",
        body="Due",
        reminder_date=organization_today(house["org"]),
        identity=identity(house["invoice"], organization_today(house["org"])),
        status="queued",
    )
    result = step(token=choose(reply, "Queue reminder"))
    assert "already exists" in result.view["text"]
    assert MessageDelivery.objects.count() == 1 and not MessageRequest.objects.exists()


def test_requested_reminder_requires_approved_template_and_respects_quiet_hours(house, settings):
    reply = reminder_preview(house, settings)
    step(token=choose(reply, "Queue reminder"))
    with (
        patch("apps.notifications.phone_messaging.approved_whatsapp_templates", return_value=[]),
        patch(
            "apps.notifications.phone_messaging.post_json",
        ) as send,
    ):
        dispatch_messages(now=timezone.now().replace(hour=12))
    send.assert_not_called()
    assert MessageDelivery.objects.get().reason == "whatsapp_template_required"
    MessageDelivery.objects.update(status="queued")
    MessagingSettings.objects.update(quiet_from="10:00", quiet_until="15:00")
    assert send_reminders().call_count == 0
    assert MessageDelivery.objects.get().available_at > timezone.now().replace(hour=12)


def test_requested_reminder_rate_limit_and_cross_workspace_scope(house, settings):
    reply = reminder_preview(house, settings)
    for _ in range(10):
        MessageRequest.objects.create(
            organization=house["org"],
            actor=house["manager"],
            source="wa_reminder",
            channel="whatsapp",
            subject="Prior request",
            body="Reminder",
            recipients=[],
            confirmed_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=1),
        )
    result = step(token=choose(reply, "Queue reminder"))
    assert "limit reached" in result.view["text"] and not MessageDelivery.objects.exists()
    from .whatsapp.reminders import preview

    other = make_lease(Organization.objects.create(name="Other workspace"))
    foreign = Invoice.objects.create(
        organization=other.organization,
        tenant=other.tenant,
        unit=other.unit,
        reference="FOREIGN-1",
        issue_date=timezone.localdate(),
        due_date=timezone.localdate(),
        total="100.00",
        status="open",
    )
    ctx = actor_context(WhatsAppBinding.objects.get(), house["org"].pk)
    conversation = WhatsAppConversation.objects.get()
    result = preview(ctx, conversation, str(foreign.public_id))
    assert "no longer needs a reminder" in result["text"]
