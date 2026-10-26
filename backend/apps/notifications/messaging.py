"""Send-only notices: frozen previews, durable delivery intent, bounded scheduling."""

from datetime import datetime, timedelta
from time import monotonic
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.access_state import email_status
from apps.billing.models import Invoice
from apps.common.mail import delivery_configured, recipient_allowed
from apps.organizations.models import OrganizationMembership
from apps.subscriptions.services import require_feature
from apps.tenants.models import Tenant

from .models import (
    MessageDelivery,
    MessageRequest,
    MessagingSettings,
    NotificationPreferences,
    ReminderPreferences,
    ReminderScan,
)

CHANNELS = ("email", "sms", "whatsapp")


def channel_readiness():
    return {
        "email": bool(
            getattr(settings, "MESSAGING_EMAIL_ENABLED", False) and delivery_configured()
        ),
        "sms": False,
        "whatsapp": False,
    }


def address(tenant, channel):
    return tenant.email if channel == "email" else tenant.phone_number


def preview(*, organization, actor, data, source="manager"):
    require_feature(organization, f"{data['channel']}_messages")
    ids = set(data["tenants"])
    tenants = list(
        Tenant.objects.filter(
            organization=organization, is_active=True, public_id__in=ids
        ).order_by("pk")
    )
    if len(tenants) != len(ids):
        raise ValidationError({"tenants": "Select active tenants in this workspace."})
    recipients = [
        {"id": str(t.public_id), "name": t.full_name, "address": address(t, data["channel"])}
        for t in tenants
    ]
    if any(not r["address"] for r in recipients):
        raise ValidationError(
            {"tenants": "Every recipient needs a contact address for this channel."}
        )
    return MessageRequest.objects.create(
        organization=organization,
        actor=actor,
        channel=data["channel"],
        subject=data["subject"],
        body=data["body"],
        recipients=recipients,
        expires_at=timezone.now() + timedelta(minutes=30),
        source=source,
    )


@transaction.atomic
def confirm(*, message, actor):
    message = (
        MessageRequest.objects.select_for_update().select_related("organization").get(pk=message.pk)
    )
    if message.actor_id != actor.pk:
        raise PermissionDenied("Only the person who previewed this message can confirm it.")
    require_feature(message.organization, f"{message.channel}_messages")
    if message.confirmed_at:
        return message
    if message.expires_at <= timezone.now():
        raise ValidationError("This preview expired. Preview the message again.")
    tenants = {
        str(t.public_id): t
        for t in Tenant.objects.filter(
            organization=message.organization,
            is_active=True,
            public_id__in=[r["id"] for r in message.recipients],
        )
    }
    rows = []
    for recipient in message.recipients:
        tenant = tenants.get(recipient["id"])
        if not tenant or address(tenant, message.channel) != recipient["address"]:
            raise ValidationError("Recipient details changed. Preview the message again.")
        # All requests start held. An explicit worker enable may send NEW email
        # intents; connecting a future API never silently releases old holds.
        ready = channel_readiness()[message.channel]
        rows.append(
            MessageDelivery(
                organization=message.organization,
                request=message,
                tenant=tenant,
                channel=message.channel,
                recipient=recipient["address"],
                subject=message.subject,
                body=message.body,
                identity=f"request:{message.public_id}:{tenant.public_id}",
                status="queued" if ready else "held",
                reason="" if ready else "delivery_not_connected",
            )
        )
    MessageDelivery.objects.bulk_create(rows)
    message.confirmed_at = timezone.now()
    message.save(update_fields=["confirmed_at", "updated_at"])
    return message


def quiet_now(organization, config, now):
    local = now.astimezone(ZoneInfo(organization.timezone)).time().replace(tzinfo=None)
    start, end = config.quiet_from, config.quiet_until
    return start <= local < end if start < end else local >= start or local < end


def schedule_reminders(*, now=None, limit=200):
    """A durable PK cursor bounds each scan; date identity prevents repeated rows."""
    now = now or timezone.now()
    limit = max(1, min(limit, 500))
    config, _ = MessagingSettings.objects.get_or_create(pk=1)
    if not config.reminders_enabled:
        return 0
    with transaction.atomic():
        scan, _ = ReminderScan.objects.get_or_create(pk=1)
        scan = ReminderScan.objects.select_for_update().get(pk=scan.pk)
        query = (
            Invoice.objects.filter(
                is_active=True,
                status__in=Invoice.UNPAID_STATUSES,
                organization__is_active=True,
                tenant__is_active=True,
                due_date__gte=now.date() - timedelta(days=91),
                due_date__lte=now.date() + timedelta(days=31),
            )
            .filter(
                Q(organization__reminderpreferences__email_enabled=True)
                | Q(organization__reminderpreferences__sms_enabled=True)
                | Q(organization__reminderpreferences__whatsapp_enabled=True)
            )
            .select_related("organization__reminderpreferences", "tenant")
            .order_by("pk")
        )
        invoices = list(query.filter(pk__gt=scan.last_invoice_id)[:limit])
        if not invoices:
            scan.last_invoice_id = 0
            scan.save(update_fields=["last_invoice_id"])
            return 0
        scan.last_invoice_id = invoices[-1].pk
        scan.save(update_fields=["last_invoice_id"])
        rows = []
        for invoice in invoices:
            pref = invoice.organization.reminderpreferences
            try:
                local = now.astimezone(ZoneInfo(invoice.organization.timezone))
            except (ZoneInfoNotFoundError, ValueError):
                continue
            if local.hour < pref.due_hour:
                continue
            days = (local.date() - invoice.due_date).days
            due = days == 0 or (pref.before_due_days > 0 and days == -pref.before_due_days)
            overdue = (
                days > 0
                and days % pref.overdue_every_days == 0
                and days // pref.overdue_every_days <= pref.overdue_repeats
            )
            if not (due or overdue) or invoice.balance <= 0:
                continue
            for channel in CHANNELS:
                if not getattr(pref, f"{channel}_enabled"):
                    continue
                recipient = address(invoice.tenant, channel)
                ready = channel_readiness()[channel]
                rows.append(
                    MessageDelivery(
                        organization=invoice.organization,
                        tenant=invoice.tenant,
                        invoice=invoice,
                        channel=channel,
                        recipient=recipient,
                        subject=f"Rent reminder: {invoice.reference}",
                        body=reminder_body(invoice),
                        identity=f"reminder:{invoice.public_id}:{local.date()}:{channel}",
                        reminder_date=local.date(),
                        status="queued" if ready and recipient else "held",
                        reason=""
                        if ready and recipient
                        else ("missing_contact" if not recipient else "delivery_not_connected"),
                    )
                )
        # Fetch identities once and bulk insert. No query per invoice/recipient.
        existing = set(
            MessageDelivery.objects.filter(identity__in=[r.identity for r in rows]).values_list(
                "identity", flat=True
            )
        )
        rows = [row for row in rows if row.identity not in existing]
        MessageDelivery.objects.bulk_create(rows, ignore_conflicts=True)
        return len(rows)


def dispatch_messages(*, now=None, limit=50):
    """No retry after an uncertain external send; SMTP acceptance is not delivery."""
    now = now or timezone.now()
    MessageDelivery.objects.filter(
        status="sending", claimed_at__lt=now - timedelta(minutes=10)
    ).update(status="review", reason="send_outcome_unknown")
    config, created = MessagingSettings.objects.get_or_create(pk=1)
    if created:
        config.refresh_from_db()
    ids = list(
        MessageDelivery.objects.filter(status="queued", available_at__lte=now)
        .order_by("available_at", "pk")
        .values_list("pk", flat=True)[: max(1, min(limit, 100))]
    )
    count = 0
    deadline = monotonic() + 45
    for pk in ids:
        if monotonic() >= deadline:
            break
        row = MessageDelivery.objects.select_related(
            "organization", "tenant", "request__actor", "invoice"
        ).get(pk=pk)
        try:
            quiet = quiet_now(row.organization, config, now)
        except (ZoneInfoNotFoundError, ValueError):
            MessageDelivery.objects.filter(pk=pk, status="queued").update(
                status="held", reason="invalid_timezone"
            )
            continue
        if quiet:
            local = now.astimezone(ZoneInfo(row.organization.timezone))
            until = datetime.combine(local.date(), config.quiet_until, tzinfo=local.tzinfo)
            if until <= local:
                until += timedelta(days=1)
            MessageDelivery.objects.filter(pk=pk, status="queued").update(available_at=until)
            continue
        reason = dispatch_block(row, config, now)
        if reason:
            MessageDelivery.objects.filter(pk=pk, status="queued").update(
                status="cancelled"
                if reason in {"invoice_no_longer_due", "recipient_changed", "permission_removed"}
                else "held",
                reason=reason,
            )
            continue
        # Atomic conditional update commits the claim before network I/O.
        if not MessageDelivery.objects.filter(pk=pk, status="queued").update(
            status="sending", claimed_at=now
        ):
            continue
        try:
            transport = get_connection(timeout=min(settings.EMAIL_TIMEOUT, 10))
            sent = EmailMessage(
                row.subject,
                row.body,
                settings.DEFAULT_FROM_EMAIL,
                [row.recipient],
                connection=transport,
                reply_to=[row.organization.email] if row.organization.email else None,
            ).send(fail_silently=False)
        except Exception:
            MessageDelivery.objects.filter(pk=pk, status="sending").update(
                status="review", reason="send_outcome_unknown"
            )
        else:
            MessageDelivery.objects.filter(pk=pk, status="sending").update(
                status="sent" if sent else "failed",
                reason="smtp_accepted" if sent else "email_not_accepted",
                sent_at=now if sent else None,
            )
            count += bool(sent)
    return count


def dispatch_block(row, config, now):
    if not row.organization.is_active or not row.tenant.is_active:
        return "permission_removed"
    if address(row.tenant, row.channel) != row.recipient:
        return "recipient_changed"
    if row.request_id:
        actor = row.request.actor
        if (
            not actor.is_active
            or email_status(actor)["required"]
            or not OrganizationMembership.objects.filter(
                organization=row.organization, user=actor, is_active=True, role="landlord"
            ).exists()
        ):
            return "permission_removed"
    try:
        require_feature(row.organization, f"{row.channel}_messages")
    except PermissionDenied:
        return "feature_unavailable"
    if row.invoice_id:
        invoice = row.invoice
        pref = ReminderPreferences.objects.filter(organization=row.organization).first()
        if (
            invoice.status not in Invoice.UNPAID_STATUSES
            or not invoice.is_active
            or invoice.balance <= 0
            or row.reminder_date != now.astimezone(ZoneInfo(row.organization.timezone)).date()
        ):
            return "invoice_no_longer_due"
        if not config.reminders_enabled or not pref or not getattr(pref, f"{row.channel}_enabled"):
            return "reminders_disabled"
        # Re-render from the fresh balance after partial payments.
        row.body = reminder_body(invoice)
        MessageDelivery.objects.filter(pk=row.pk, status="queued").update(body=row.body)
    pref = (
        NotificationPreferences.objects.filter(user_id=row.tenant.user_id).first()
        if row.tenant.user_id
        else None
    )
    if pref and not getattr(pref, f"{row.channel}_enabled"):
        return "recipient_opted_out"
    if row.channel == "whatsapp":
        return "whatsapp_consent_template_required"
    if not channel_readiness()[row.channel]:
        return "delivery_not_connected"
    if row.channel == "email" and not recipient_allowed(row.recipient):
        return "recipient_restricted"
    return ""


def reminder_body(invoice):
    return (
        f"{invoice.reference}: {invoice.organization.currency} "
        f"{invoice.balance:.2f} outstanding. Due {invoice.due_date}. "
        "Please check your Dwella payments page."
    )
