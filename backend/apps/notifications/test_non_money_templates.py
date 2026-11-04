from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.maintenance.services import create_request, start_request
from apps.organizations.models import Organization, OrganizationMembership

from . import test_operational as operational
from .models import NotificationPhoneLink, OperationalDelivery, PhoneMessagingConsent
from .non_money_templates import enqueue_connection
from .operational import enqueue
from .test_operational import (
    body_values,
    client,
    opted_in,
    send_outside_window,
    tenant_phone,
)

pytestmark = pytest.mark.django_db(transaction=True)
APPROVED = {
    f"{name}:en"
    for name in (
        "dwella_repair_reported",
        "dwella_repair_update",
        "dwella_lease_ready",
        "dwella_connect_whatsapp",
    )
}


@pytest.fixture(name="house")
def notification_house(settings):
    return operational.house.__wrapped__(settings)


def repair(house, **overrides):
    lease = house[3]
    return create_request(
        organization=house[0],
        tenant=lease.tenant,
        property=lease.unit.property,
        title="Leaking tap",
        description="Private repair description",
        **{"unit": lease.unit, **overrides},
    )


def prepare(house, settings):
    settings.WHATSAPP_OPERATIONAL_TEMPLATE = ""
    tenant_phone(house)
    opted_in(house[1], "+260971234560")
    opted_in(house[2])


def test_reported_template_only_addresses_manager_and_public_facts(house, settings):
    prepare(house, settings)
    job = repair(house)
    payloads = send_outside_window(APPROVED)
    assert [p["template"]["name"] for p in payloads] == ["dwella_repair_reported"]
    assert body_values(payloads[0]) == [
        "there",
        house[3].tenant.full_name,
        job.reference,
        job.unit.name,
    ]
    assert "Private repair description" not in str(payloads)


def test_repair_update_template_only_addresses_tenant_and_current_status(house, settings):
    prepare(house, settings)
    job = repair(house)
    OperationalDelivery.objects.all().delete()
    job = start_request(job)
    payloads = send_outside_window(APPROVED)
    assert [p["template"]["name"] for p in payloads] == ["dwella_repair_update"]
    assert body_values(payloads[0]) == [
        house[3].tenant.full_name,
        job.reference,
        job.unit.name,
        "In progress",
    ]


def test_common_area_report_does_not_require_unit(house, settings):
    prepare(house, settings)
    repair(house, unit=None)
    assert body_values(send_outside_window(APPROVED)[0])[-1] == "Common areas"


def test_lease_ready_template_only_for_pending_signature_tenant(house, settings):
    prepare(house, settings)
    lease = house[3]
    lease.status = "pending_signature"
    lease.save()
    payloads = send_outside_window(APPROVED)
    assert [p["template"]["name"] for p in payloads] == ["dwella_lease_ready"]
    assert body_values(payloads[0]) == [lease.tenant.full_name, house[0].name, lease.unit.name]


@pytest.mark.parametrize(
    "change",
    [
        "approval",
        "language",
        "consent",
        "membership",
        "workspace",
        "superseded",
        "reassigned",
        "allowlist",
        "kill_switch",
    ],
)
def test_non_money_delivery_rechecks_live_guards(house, settings, change):
    prepare(house, settings)
    job = repair(house)
    approved = APPROVED
    if change == "approval":
        approved = set()
    elif change == "language":
        approved = {name.replace(":en", ":fr") for name in APPROVED}
    elif change == "consent":
        PhoneMessagingConsent.objects.update(allowed=False)
    elif change == "membership":
        OrganizationMembership.objects.update(is_active=False)
    elif change == "workspace":
        Organization.objects.filter(pk=house[0].pk).update(is_active=False)
    elif change == "superseded":
        type(job).objects.filter(pk=job.pk).update(status="completed")
    elif change == "reassigned":
        OperationalDelivery.objects.update(organization=Organization.objects.create(name="Other"))
    if change in {"allowlist", "kill_switch"}:
        guard = "phone_allowed" if change == "allowlist" else "whatsapp_ready"
        with patch(
            f"apps.notifications.operational.{guard}",
            return_value=False,
        ):
            # Exercise the real readiness guard rather than the mocked send helper.
            from .operational import dispatch_operational

            with patch("apps.notifications.operational.post_json") as send:
                dispatch_operational(now=(timezone.now() + timedelta(days=1)).replace(hour=12))
            send.assert_not_called()
    else:
        assert send_outside_window(approved) == []


def connection(house, user=None, consent=True):
    user = user or house[2]
    return NotificationPhoneLink.objects.create(
        user=user,
        channel="whatsapp",
        phone="+260971234567",
        token_hash="token",
        expires_at=timezone.now() + timedelta(minutes=10),
        verified_at=timezone.now(),
        consumed_at=timezone.now(),
        notification_consent=consent,
    )


def test_connection_ack_is_deduplicated_and_uses_exact_verified_number(house, settings):
    settings.WHATSAPP_OPERATIONAL_TEMPLATE = ""
    opted_in(house[2])
    link = connection(house)
    enqueue_connection(link, house[0])
    enqueue_connection(link, house[0])
    assert OperationalDelivery.objects.count() == 1
    payloads = send_outside_window(APPROVED)
    assert len(payloads) == 1 and payloads[0]["template"]["name"] == "dwella_connect_whatsapp"
    assert payloads[0]["to"] == "260971234567"
    assert len(body_values(payloads[0])) == 1
    assert send_outside_window(APPROVED) == []


@pytest.mark.parametrize(
    "change",
    [
        "stop",
        "different_number",
        "membership",
        "unverified",
        "unconsumed",
        "other_user",
        "new_connection",
        "approval",
    ],
)
def test_connection_ack_cannot_bypass_current_link_consent_or_authority(house, settings, change):
    settings.WHATSAPP_OPERATIONAL_TEMPLATE = ""
    consent = opted_in(house[2])
    link = connection(house)
    enqueue_connection(link, house[0])
    if change == "stop":
        consent.allowed = False
        consent.save()
    elif change == "different_number":
        consent.phone = "+260971234568"
        consent.save()
    elif change == "membership":
        OrganizationMembership.objects.filter(user=house[2]).update(is_active=False)
    elif change in {"unverified", "unconsumed"}:
        setattr(link, "verified_at" if change == "unverified" else "consumed_at", None)
        link.save()
    elif change == "other_user":
        link.user = house[1]
        link.save()
    elif change == "new_connection":
        link.pk = None
        link.token_hash = "new-token"
        link.consumed_at = timezone.now() + timedelta(seconds=1)
        link.save()
    assert send_outside_window(set() if change == "approval" else APPROVED) == []


def test_actions_only_connection_does_not_gain_notification_consent(house):
    link = connection(house, consent=False)
    enqueue_connection(link, house[0])
    assert not OperationalDelivery.objects.exists()


def test_completion_enqueues_ack_without_network(house):
    link = connection(house)
    link.consumed_at = None
    link.save()
    with patch("apps.notifications.operational.post_json") as send:
        response = client(house[2]).post(
            "/api/v1/notifications/phone-link/",
            {"channel": "whatsapp", "complete": link.pk},
            format="json",
        )
    assert response.status_code == 200, response.data
    assert OperationalDelivery.objects.filter(event="whatsapp.connected").count() == 1
    send.assert_not_called()


def test_no_template_for_public_comment_or_unsupported_audience(house, settings):
    prepare(house, settings)
    job = repair(house)
    OperationalDelivery.objects.all().delete()
    enqueue(job, "repair.comment")
    assert send_outside_window(APPROVED) == []
