"""One manager-requested reminder, confirmed against the current invoice balance."""

from datetime import timedelta

from django.core.exceptions import ValidationError as InvalidStoredValue
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.access_state import email_status
from apps.audit.models import AuditEvent
from apps.billing.models import Invoice
from apps.notifications.models import MessageDelivery, MessageRequest, PhoneMessagingConsent
from apps.notifications.phone_messaging import normalize_phone
from apps.organizations.models import OrganizationMembership
from apps.reports.common import organization_today

SOURCE = "wa_reminder"
HOURLY_LIMIT = 10


def eligible(ctx):
    if ctx.role != "landlord":
        raise PermissionDenied("Only property managers can request reminders.")
    return (
        ctx.scope(Invoice.objects.all())
        .filter(
            status__in=Invoice.UNPAID_STATUSES,
            is_opening_balance=False,
            tenant__is_active=True,
            tenant__organization=ctx.organization,
        )
        .select_related("tenant")
    )


def consented(invoice):
    tenant = invoice.tenant
    return bool(
        tenant.user_id
        and tenant.user.is_active
        and not email_status(tenant.user)["required"]
        and OrganizationMembership.objects.filter(
            organization_id=invoice.organization_id,
            user_id=tenant.user_id,
            is_active=True,
            role="tenant",
        ).exists()
        and PhoneMessagingConsent.objects.filter(
            channel="whatsapp",
            phone=normalize_phone(tenant.phone_number),
            user_id=tenant.user_id,
            source="verified_link",
            allowed=True,
            revoked_at__isnull=True,
        ).exists()
    )


def identity(invoice, day):
    # Shares the scheduler's identity, so on-demand and automatic work never double-send today.
    return f"reminder:{invoice.public_id}:{day}:whatsapp"


def preview(ctx, conversation, target):
    from .conversation import choice, invoice_snapshot, menu, response

    invoice = eligible(ctx).filter(public_id=target).first()
    if not invoice or invoice.balance <= 0:
        return menu(ctx, conversation, "That invoice no longer needs a reminder.")
    if not consented(invoice):
        return menu(
            ctx, conversation, "This tenant has not connected and opted in to WhatsApp notices."
        )
    conversation.draft = {
        "intent": "reminder",
        "invoice": str(invoice.public_id),
        "snapshot": invoice_snapshot([invoice]),
        "recipient": invoice.tenant.phone_number,
    }
    return response(
        f"Request WhatsApp reminder?\nTo: {invoice.tenant.full_name}\n"
        f"Number: {invoice.tenant.phone_number}\nInvoice: {invoice.reference}\n"
        f"Outstanding: {ctx.organization.currency} {invoice.balance:,.2f}\n"
        f"Due: {invoice.due_date}\nSending follows notification consent and quiet hours.",
        [
            choice(conversation, "Queue reminder", "reminder_confirm", member=ctx.membership),
            choice(conversation, "Cancel", "menu", member=ctx.membership),
        ],
        {"invoices": invoice_snapshot([invoice])},
    )


@transaction.atomic
def confirm(ctx, conversation):
    from .conversation import invoice_snapshot, menu

    draft = conversation.draft
    if draft.get("intent") != "reminder":
        raise ValidationError("Preview a reminder first.")
    invoice = eligible(ctx).filter(public_id=draft["invoice"]).first()
    if not invoice or invoice.balance <= 0 or not consented(invoice):
        conversation.draft = {}
        return menu(ctx, conversation, "The invoice or recipient changed. Nothing was queued.")
    if (
        invoice_snapshot([invoice]) != draft["snapshot"]
        or invoice.tenant.phone_number != draft["recipient"]
    ):
        return preview(ctx, conversation, draft["invoice"])
    day = organization_today(ctx.organization)
    key = identity(invoice, day)
    if MessageDelivery.objects.filter(identity=key).exists():
        conversation.draft = {}
        return menu(ctx, conversation, "A reminder already exists for this invoice today.")
    if (
        MessageRequest.objects.filter(
            actor=ctx.user,
            source=SOURCE,
            created_at__gte=timezone.now() - timedelta(hours=1),
        ).count()
        >= HOURLY_LIMIT
    ):
        return menu(ctx, conversation, "Reminder request limit reached. Try again later.")
    from apps.notifications.messaging import reminder_body

    body = reminder_body(invoice, channel="whatsapp")
    request = MessageRequest.objects.create(
        organization=ctx.organization,
        actor=ctx.user,
        source=SOURCE,
        channel="whatsapp",
        subject=f"Rent reminder: {invoice.reference}",
        body=body,
        recipients=[
            {
                "id": str(invoice.tenant.public_id),
                "name": invoice.tenant.full_name,
                "address": draft["recipient"],
                "binding_id": ctx.binding.pk,
                "binding_generation": str(ctx.binding.generation),
            }
        ],
        confirmed_at=timezone.now(),
        expires_at=timezone.now() + timedelta(days=1),
    )
    _, created = MessageDelivery.objects.get_or_create(
        identity=key,
        defaults={
            "organization": ctx.organization,
            "tenant": invoice.tenant,
            "invoice": invoice,
            "request": request,
            "channel": "whatsapp",
            "recipient": draft["recipient"],
            "subject": request.subject,
            "body": body,
            "reminder_date": day,
            "status": "queued",
        },
    )
    if not created:
        request.delete()
    else:
        AuditEvent.objects.create(
            actor=ctx.user,
            organization=ctx.organization,
            action="notifications.whatsapp_reminder_queued",
            resource_type="billing.invoice",
            resource_id=str(invoice.public_id),
        )
    conversation.draft = {}
    return menu(
        ctx,
        conversation,
        "Reminder queued. This does not mean it has been delivered."
        if created
        else "A reminder already exists for this invoice today.",
    )


def current(row):
    """Recheck the initiating link and tenant opt-in immediately before dispatch."""
    from .access import actor_context
    from .models import WhatsAppBinding

    if not row.invoice_id or row.channel != "whatsapp" or not row.request.confirmed_at:
        return False
    try:
        recipient = row.request.recipients[0]
        binding = WhatsAppBinding.objects.select_related("user").get(
            pk=recipient["binding_id"],
            user_id=row.request.actor_id,
            generation=recipient["binding_generation"],
            revoked_at__isnull=True,
        )
        ctx = actor_context(binding, row.organization_id)
        invoice = eligible(ctx).filter(pk=row.invoice_id, tenant_id=row.tenant_id).first()
        if (
            not invoice
            or invoice.balance <= 0
            or invoice.tenant.phone_number != row.recipient
            or not consented(invoice)
        ):
            return False
        invoice.organization = row.organization
        row.invoice = invoice
        row.tenant = invoice.tenant
        return True
    except (
        PermissionDenied,
        InvalidStoredValue,
        KeyError,
        IndexError,
        ValueError,
        TypeError,
        WhatsAppBinding.DoesNotExist,
    ):
        return False
