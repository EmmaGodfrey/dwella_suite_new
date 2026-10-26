"""Send-only notices: frozen previews, durable delivery intent, bounded scheduling."""

from datetime import datetime, time, timedelta
from time import monotonic
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.db import transaction
from django.db.models import F, Q
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
)

CHANNELS = ("email", "sms", "whatsapp")
ALL_TENANTS_LIMIT = 2000


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
    active = Tenant.objects.filter(organization=organization, is_active=True).order_by("pk")
    skipped = 0
    if data.get("all_tenants"):
        tenants = list(active[: ALL_TENANTS_LIMIT + 1])
        if len(tenants) > ALL_TENANTS_LIMIT:
            raise ValidationError({"all_tenants": "Too many tenants for one notice."})
        # Everyone reachable on this channel; the preview reports who was left out.
        reachable = [t for t in tenants if address(t, data["channel"])]
        skipped = len(tenants) - len(reachable)
        tenants = reachable
        if not tenants:
            raise ValidationError(
                {"all_tenants": "No tenant has a contact address for this channel."}
            )
    else:
        ids = set(data["tenants"])
        tenants = list(active.filter(public_id__in=ids))
        if len(tenants) != len(ids):
            raise ValidationError({"tenants": "Select active tenants in this workspace."})
        if any(not address(t, data["channel"]) for t in tenants):
            raise ValidationError(
                {"tenants": "Every recipient needs a contact address for this channel."}
            )
    recipients = [
        {"id": str(t.public_id), "name": t.full_name, "address": address(t, data["channel"])}
        for t in tenants
    ]
    message = MessageRequest.objects.create(
        organization=organization,
        actor=actor,
        channel=data["channel"],
        subject=data["subject"],
        body=data["body"],
        recipients=recipients,
        expires_at=timezone.now() + timedelta(minutes=30),
        source=source,
    )
    message.skipped = skipped
    return message


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


def reminder_dates(pref, today):
    """Due dates that get a reminder today: before due, on the day, then each overdue repeat."""
    dates = {today}
    if pref.before_due_days:
        dates.add(today + timedelta(days=pref.before_due_days))
    for repeat in range(1, pref.overdue_repeats + 1):
        dates.add(today - timedelta(days=repeat * pref.overdue_every_days))
    return dates


def due_moment(pref, local_date):
    """The workspace's reminder hour on a local date, as an aware datetime."""
    tz = ZoneInfo(pref.organization.timezone)
    return datetime.combine(local_date, time(pref.due_hour), tzinfo=tz)


def schedule_reminders(*, now=None, limit=500):
    """Bounded and resumable over workspaces and invoices alike.

    Each workspace stores when its next run is due, so finished workspaces are never
    loaded. A run touches at most `limit` workspaces and handles at most `limit`
    invoices; unfinished work keeps its due time and continues on the next run.
    Only connected channels are scheduled: a held reminder would never be released.
    """
    now = now or timezone.now()
    config, _ = MessagingSettings.objects.get_or_create(pk=1)
    ready = [channel for channel, ok in channel_readiness().items() if ok]
    if not config.reminders_enabled or not ready:
        return 0
    enabled = Q()
    for channel in ready:
        enabled |= Q(**{f"{channel}_enabled": True})
    budget = max(1, min(limit, 2000))
    due = (
        ReminderPreferences.objects.filter(enabled, organization__is_active=True)
        .filter(Q(next_run_at__isnull=True) | Q(next_run_at__lte=now))
        .select_related("organization")
        .order_by(F("next_run_at").asc(nulls_first=True), "pk")[:budget]
    )
    count = 0
    for pref in due:
        if budget <= 0:
            break
        budget -= 1
        try:
            local = now.astimezone(ZoneInfo(pref.organization.timezone))
        except (ZoneInfoNotFoundError, ValueError):
            # Park it for a day rather than reloading it on every run.
            ReminderPreferences.objects.filter(pk=pref.pk).update(
                next_run_at=now + timedelta(days=1)
            )
            continue
        if local.hour < pref.due_hour:
            ReminderPreferences.objects.filter(pk=pref.pk).update(
                next_run_at=due_moment(pref, local.date())
            )
            continue
        created, used = schedule_workspace(pref.pk, local.date(), ready, max(1, budget))
        count += created
        budget -= used
    return count


@transaction.atomic
def schedule_workspace(pk, today, ready, budget):
    """One bounded slice of a workspace's daily run. Returns (rows created, invoices used)."""
    pref = ReminderPreferences.objects.select_for_update().select_related("organization").get(pk=pk)
    if pref.run_date != today:
        # A run left unfinished yesterday is not resumed; those reminders would be stale.
        pref.run_date, pref.run_after_id = today, 0
    if pref.run_after_id is None:
        pref.next_run_at = due_moment(pref, today + timedelta(days=1))
        pref.save(update_fields=["run_date", "next_run_at"])
        return 0, 0
    organization = pref.organization
    channels = [channel for channel in ready if getattr(pref, f"{channel}_enabled")]
    invoices = list(
        Invoice.objects.filter(
            organization=organization,
            is_active=True,
            status__in=Invoice.UNPAID_STATUSES,
            tenant__is_active=True,
            due_date__in=reminder_dates(pref, today),
            pk__gt=pref.run_after_id,
        )
        .select_related("tenant")
        .order_by("pk")[:budget]
    )
    if len(invoices) == budget:
        # More may remain; stay due so the next run continues from here.
        pref.run_after_id = invoices[-1].pk
    else:
        pref.run_after_id = None
        pref.next_run_at = due_moment(pref, today + timedelta(days=1))
    pref.save(update_fields=["run_date", "run_after_id", "next_run_at"])
    rows = []
    for invoice in invoices:
        if invoice.balance <= 0:
            continue
        invoice.organization = organization
        for channel in channels:
            recipient = address(invoice.tenant, channel)
            rows.append(
                MessageDelivery(
                    organization=organization,
                    tenant=invoice.tenant,
                    invoice=invoice,
                    channel=channel,
                    recipient=recipient,
                    subject=f"Rent reminder: {invoice.reference}",
                    body=reminder_body(invoice),
                    identity=f"reminder:{invoice.public_id}:{today}:{channel}",
                    reminder_date=today,
                    status="queued" if recipient else "held",
                    reason="" if recipient else "missing_contact",
                )
            )
    existing = set(
        MessageDelivery.objects.filter(identity__in=[r.identity for r in rows]).values_list(
            "identity", flat=True
        )
    )
    rows = [row for row in rows if row.identity not in existing]
    MessageDelivery.objects.bulk_create(rows, ignore_conflicts=True)
    return len(rows), len(invoices)


def email_budget(now):
    """Rolling 24-hour allowance; every claimed send counts, including uncertain ones."""
    used = MessageDelivery.objects.filter(
        channel="email", claimed_at__gte=now - timedelta(hours=24)
    ).count()
    return max(0, settings.MESSAGING_EMAIL_DAILY_LIMIT - used)


def claim(pk, now):
    """Check the allowance and claim under one lock, so overlapping runs cannot overspend.

    Returns None when the allowance is used up, else whether this run won the claim.
    The claim commits before any network I/O.
    """
    with transaction.atomic():
        MessagingSettings.objects.select_for_update().get(pk=1)
        if not email_budget(now):
            return None
        return bool(
            MessageDelivery.objects.filter(pk=pk, status="queued").update(
                status="sending", claimed_at=now
            )
        )


def dispatch_messages(*, now=None, limit=50):
    """No retry after an uncertain external send; SMTP acceptance is not delivery.

    One mail connection serves the whole batch. Authority is re-checked for every
    message. Messages over the daily email allowance wait in the queue.
    """
    now = now or timezone.now()
    MessageDelivery.objects.filter(
        status="sending", claimed_at__lt=now - timedelta(minutes=10)
    ).update(status="review", reason="send_outcome_unknown")
    config, created = MessagingSettings.objects.get_or_create(pk=1)
    if created:
        config.refresh_from_db()
    size = min(max(1, min(limit, 100)), email_budget(now))
    if not size:
        return 0
    ids = list(
        MessageDelivery.objects.filter(status="queued", available_at__lte=now)
        .order_by("available_at", "pk")
        .values_list("pk", flat=True)[:size]
    )
    count = 0
    transport = None
    deadline = monotonic() + 45
    try:
        for pk in ids:
            if monotonic() >= deadline:
                break
            row = MessageDelivery.objects.select_related(
                "organization",
                "tenant__user__notificationpreferences",
                "request__actor",
                "invoice",
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
                    status="cancelled" if reason in FINAL_REASONS else "held",
                    reason=reason,
                )
                continue
            if transport is None:
                transport = get_connection(timeout=min(settings.EMAIL_TIMEOUT, 10))
                try:
                    transport.open()
                except Exception:
                    # Nothing was claimed, so the batch waits for the next run.
                    transport = None
                    break
            claimed = claim(pk, now)
            if claimed is None:
                break
            if not claimed:
                continue
            try:
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
                close_quietly(transport)
                transport = None
            else:
                MessageDelivery.objects.filter(pk=pk, status="sending").update(
                    status="sent" if sent else "failed",
                    reason="smtp_accepted" if sent else "email_not_accepted",
                    sent_at=now if sent else None,
                )
                count += bool(sent)
    finally:
        close_quietly(transport)
    return count


FINAL_REASONS = {"invoice_no_longer_due", "recipient_changed", "permission_removed"}


def close_quietly(transport):
    if transport is None:
        return
    try:
        transport.close()
    except Exception:
        pass


def feature_available(organization, channel):
    try:
        require_feature(organization, f"{channel}_messages")
    except PermissionDenied:
        return False
    return True


def actor_allowed(organization, actor):
    return (
        actor.is_active
        and not email_status(actor)["required"]
        and OrganizationMembership.objects.filter(
            organization=organization, user=actor, is_active=True, role="landlord"
        ).exists()
    )


def dispatch_block(row, config, now):
    """Re-check authority immediately before each send; nothing is cached across messages."""
    organization = row.organization
    if not organization.is_active or not row.tenant.is_active:
        return "permission_removed"
    if address(row.tenant, row.channel) != row.recipient:
        return "recipient_changed"
    if row.request_id and not actor_allowed(organization, row.request.actor):
        return "permission_removed"
    if not feature_available(organization, row.channel):
        return "feature_unavailable"
    if row.invoice_id:
        invoice = row.invoice
        pref = ReminderPreferences.objects.filter(organization=organization).first()
        today = now.astimezone(ZoneInfo(organization.timezone)).date()
        # A reminder held back by quiet hours or the daily allowance may go a day late.
        if (
            invoice.status not in Invoice.UNPAID_STATUSES
            or not invoice.is_active
            or invoice.balance <= 0
            or not today - timedelta(days=1) <= row.reminder_date <= today
        ):
            return "invoice_no_longer_due"
        if not config.reminders_enabled or not pref or not getattr(pref, f"{row.channel}_enabled"):
            return "reminders_disabled"
        # Re-render from the fresh balance after partial payments.
        invoice.organization = organization
        row.body = reminder_body(invoice)
        MessageDelivery.objects.filter(pk=row.pk, status="queued").update(body=row.body)
    if row.tenant.user_id and not tenant_accepts(row.tenant.user, row.channel):
        return "recipient_opted_out"
    if row.channel == "whatsapp":
        return "whatsapp_consent_template_required"
    if not channel_readiness()[row.channel]:
        return "delivery_not_connected"
    if row.channel == "email" and not recipient_allowed(row.recipient):
        return "recipient_restricted"
    return ""


def tenant_accepts(user, channel):
    # A tenant who never saved preferences gets the same defaults Settings shows them.
    pref = getattr(user, "notificationpreferences", None) or NotificationPreferences()
    return getattr(pref, f"{channel}_enabled")


def reminder_body(invoice):
    return (
        f"{invoice.reference}: {invoice.organization.currency} "
        f"{invoice.balance:.2f} outstanding. Due {invoice.due_date}. "
        "Please check your Dwella payments page."
    )
