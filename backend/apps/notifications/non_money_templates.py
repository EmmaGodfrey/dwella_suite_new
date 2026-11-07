"""Fixed non-payment template parameters; authority stays in the outbox dispatcher."""

from django.db import transaction

from apps.accounts.access_state import email_status
from apps.organizations.models import OrganizationMembership

from .models import NotificationPhoneLink, OperationalDelivery

CONNECTION_TARGET = "notifications.notificationphonelink"


def non_money_template(row, target):
    name = None
    values = ()
    if row.target_model == "maintenance.maintenancerequest":
        if row.event == "repair.created" and row.audience == "manager":
            name = "dwella_repair_reported"
            values = (
                row.recipient_user.get_full_name() or "there",
                target.tenant.full_name if target.tenant else "No linked tenant",
                target.reference,
                target.unit.name if target.unit else "Common areas",
            )
        elif row.event == "repair.status" and row.audience == "tenant":
            name = "dwella_repair_update"
            values = (
                target.tenant.full_name,
                target.reference,
                target.unit.name if target.unit else "Common areas",
                target.get_status_display(),
            )
    elif (
        row.target_model == "leases.lease"
        and row.event == "lease.pending_signature"
        and row.audience == "tenant"
        and target.status == "pending_signature"
    ):
        name = "dwella_lease_ready"
        values = (target.tenant.full_name, row.organization.name, target.unit.name)
    elif row.target_model == CONNECTION_TARGET and row.event == "whatsapp.connected":
        name = "dwella_connect_whatsapp"
        values = (row.recipient_user.get_full_name() or "there",)
    if name:
        return name, [" ".join(str(value).split()) for value in values]
    return None


def enqueue_connection(link, organization):
    """One optional acknowledgement per completed, consented verification; no network I/O."""
    if link.channel != "whatsapp" or not link.notification_consent or not link.consumed_at:
        return
    role = (
        OrganizationMembership.objects.filter(
            organization=organization,
            user_id=link.user_id,
            is_active=True,
            role__in=["landlord", "tenant"],
        )
        .values_list("role", flat=True)
        .first()
    )
    if not role:
        return
    OperationalDelivery.objects.get_or_create(
        identity=f"whatsapp.connected:{link.pk}",
        defaults={
            "organization": organization,
            "event": "whatsapp.connected",
            "target_model": CONNECTION_TARGET,
            "target_id": link.pk,
            "recipient_user_id": link.user_id,
            "audience": "manager" if role == "landlord" else "tenant",
            "channel": "whatsapp",
        },
    )


def connection_authorised(row, link):
    user = row.recipient_user
    return bool(
        link
        and row.event == "whatsapp.connected"
        and row.channel == "whatsapp"
        and row.organization.is_active
        and user
        and user.pk == link.user_id
        and user.is_active
        and not user.is_staff
        and not user.is_superuser
        and not email_status(user)["required"]
        and link.channel == "whatsapp"
        and link.notification_consent
        and link.consumed_at
        and link.verified_at
        and not NotificationPhoneLink.objects.filter(
            user_id=link.user_id,
            channel="whatsapp",
            consumed_at__gt=link.consumed_at,
        ).exists()
        and row.audience in {"manager", "tenant"}
        and OrganizationMembership.objects.filter(
            organization=row.organization,
            user=user,
            is_active=True,
            role="landlord" if row.audience == "manager" else "tenant",
        ).exists()
    )


def safely_enqueue_connection(link, organization):
    # Keep an optional acknowledgement failure from undoing a successful connection.
    import logging

    try:
        with transaction.atomic():
            enqueue_connection(link, organization)
    except Exception:
        logging.getLogger(__name__).exception("Could not queue WhatsApp connection notice")
