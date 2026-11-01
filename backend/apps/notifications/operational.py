"""Transactional notices: bounded outbox, live authority and conservative delivery."""

import logging
import uuid
from datetime import timedelta
from time import monotonic
from types import SimpleNamespace
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.access_state import email_status
from apps.common.email_router import EmailQuotaExceeded
from apps.common.mail import delivery_configured, recipient_allowed
from apps.common.provider_http import ProviderRejected, post_json
from apps.organizations.models import OrganizationMembership

from .actor_context import current_actor
from .models import (
    NotificationPreferences,
    OperationalDelivery,
    OperationalScan,
    PhoneMessagingConsent,
)
from .phone_messaging import normalize_phone, phone_allowed, send_sms, sms_ready, whatsapp_ready

logger = logging.getLogger(__name__)

TARGETS = {
    "billing.depositdeduction",
    "billing.depositentry",
    "billing.invoice",
    "billing.payment",
    "leases.lease",
    "maintenance.maintenancerequest",
    "maintenance.maintenanceupdate",
    "payments.collection",
    "payments.payout",
    "payments.withdrawal",
}
TITLES = {
    "invoice.issued": "Invoice available",
    "invoice.void": "Invoice cancelled",
    "invoice.reminder": "Rent reminder",
    "payment.confirmed": "Payment received",
    "payment.corrected": "Payment corrected",
    "lease.pending_signature": "Lease awaiting signature",
    "lease.active": "Lease activated",
    "lease.ended": "Lease ended",
    "lease.expiry": "Lease ending",
    "repair.created": "Repair reported",
    "repair.status": "Repair progress",
    "repair.comment": "New repair comment",
    "collection.failed": "Payment attempt failed",
    "collection.review": "Payment needs review",
    "collection.expired": "Payment attempt expired",
    "withdrawal.successful": "Withdrawal delivered",
    "withdrawal.failed": "Withdrawal failed",
    "withdrawal.review": "Withdrawal needs attention",
    "payout.successful": "Payout delivered",
    "payout.failed": "Payout failed",
    "payout.review": "Payout needs attention",
    "withdrawal.queued": "Withdrawal requested",
    "withdrawal.pending": "Withdrawal processing",
    "withdrawal.cancelled": "Withdrawal cancelled",
    "deposit.deduction_proposed": "Deposit deduction proposed",
    "deposit.deduction_answered": "Tenant answered a deposit deduction",
    "deposit.deduction_applied": "Deposit deduction applied",
    "deposit.refund_recorded": "Deposit refund recorded",
}


def context(target):
    """Return the organisation and subject tenant; never infer a recipient from a phone."""
    label = target._meta.label_lower
    if label == "maintenance.maintenanceupdate":
        return target.request.organization, target.request.tenant
    if label == "payments.payout":
        return target.collection.organization, None
    if label == "payments.collection":
        return target.organization, target.invoice.tenant
    if label in ("billing.depositdeduction", "billing.depositentry"):
        return target.organization, target.lease.tenant
    return target.organization, getattr(target, "tenant", None)


def enqueue(
    target,
    event,
    *,
    suffix="",
    state="",
    managers_only=False,
    tenant_only=False,
    optional=True,
    available_at=None,
    actor=None,
):
    if event not in TITLES or target._meta.label_lower not in TARGETS:
        raise ValueError("Unsupported operational event")
    organization, tenant = context(target)
    actor = actor or current_actor()
    # Draft imported records without a tenancy are never sent to an arbitrary contact.
    recipients = []
    if not tenant_only and event != "invoice.issued":
        recipients.extend(
            ("manager", user, None)
            for user in apps.get_model(settings.AUTH_USER_MODEL)
            .objects.filter(
                organization_memberships__organization=organization,
                organization_memberships__role="landlord",
                organization_memberships__is_active=True,
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            .order_by("pk")[:2000]
        )
    if tenant and not managers_only:
        recipients.append(("tenant", tenant.user, tenant))
    user_ids = {u.pk for _, u, _ in recipients if u}
    preferences = {
        p.user_id: p for p in NotificationPreferences.objects.filter(user_id__in=user_ids)
    }
    rows = []
    event_key = f"{target._meta.label_lower}:{target.pk}:{event}:{suffix or state}"
    for audience, user, subject in recipients:
        if actor and user and user.pk == actor.pk:
            continue
        pref = preferences.get(user.pk) if user else None
        channels = ["email"]
        for channel in ("sms", "whatsapp"):
            if optional and pref and getattr(pref, f"{channel}_enabled"):
                channels.append(channel)
        for channel in channels:
            recipient = (subject.email if subject else user.email) if channel == "email" else ""
            if channel == "email" and not recipient.strip():
                continue
            recipient_key = subject.pk if subject else user.pk
            rows.append(
                OperationalDelivery(
                    organization=organization,
                    identity=f"{event_key}:{audience}:{recipient_key}:{channel}",
                    event=event,
                    target_model=target._meta.label_lower,
                    target_id=target.pk,
                    target_state=state,
                    recipient_user=user,
                    tenant=subject,
                    audience=audience,
                    channel=channel,
                    recipient=recipient,
                    available_at=available_at or timezone.now(),
                )
            )
    OperationalDelivery.objects.bulk_create(rows, ignore_conflicts=True)


def target_for(row):
    if row.target_model not in TARGETS:
        return None
    model = apps.get_model(row.target_model)
    related = {
        "maintenance.maintenanceupdate": ("request__organization", "request__tenant"),
        "payments.payout": ("collection__organization", "collection__invoice"),
        "payments.collection": ("organization", "invoice__tenant"),
        "billing.payment": ("organization", "invoice", "tenant"),
        "billing.invoice": ("organization", "tenant"),
        "leases.lease": ("organization", "tenant", "unit"),
        "maintenance.maintenancerequest": ("organization", "tenant", "unit"),
        "payments.withdrawal": ("organization",),
        "billing.depositdeduction": ("organization", "lease__tenant"),
        "billing.depositentry": ("organization", "lease__tenant"),
    }[row.target_model]
    return model.objects.select_related(*related).filter(pk=row.target_id).first()


def authorised(row, target):
    if not target or not row.organization.is_active:
        return False
    org, tenant = context(target)
    if org.pk != row.organization_id or not getattr(target, "is_active", True):
        return False
    if row.audience == "manager":
        user = row.recipient_user
        return bool(
            user
            and user.is_active
            and not user.is_staff
            and not user.is_superuser
            and not email_status(user)["required"]
            and OrganizationMembership.objects.filter(
                organization_id=org.pk,
                user=user,
                role="landlord",
                is_active=True,
            ).exists()
        )
    if not tenant or not tenant.is_active or tenant.pk != row.tenant_id:
        return False
    # A reassigned tenant record must not send old notices to the former account.
    if tenant.user_id != row.recipient_user_id:
        return False
    if row.recipient_user_id:
        user = row.recipient_user
        if not user.is_active or email_status(user)["required"]:
            return False
        if not OrganizationMembership.objects.filter(
            organization=org,
            user=user,
            role="tenant",
            is_active=True,
        ).exists():
            return False
    if row.target_model == "maintenance.maintenanceupdate":
        return not target.is_internal and target.request.is_active
    return True


def content(row, target):
    title = TITLES[row.event]
    currency = row.organization.currency
    label = row.target_model
    if label == "billing.payment":
        if row.event == "payment.confirmed" and target.reversed_at:
            return None
        detail = (
            f"{target.tenant.full_name}: {currency} {target.amount:.2f}. "
            f"Receipt {target.receipt_number}; invoice {target.invoice.reference}. "
            f"Paid on {target.paid_on}."
        )
        path = f"/billing/receipts/{target.public_id}"
    elif label == "billing.invoice":
        if row.event == "invoice.issued" and target.status == "void":
            return None
        if row.event == "invoice.reminder" and (
            target.status not in target.UNPAID_STATUSES or target.balance <= 0
        ):
            return None
        detail = (
            f"{target.tenant.full_name}: invoice {target.reference}, "
            f"{currency} {target.total:.2f}; outstanding {currency} {target.balance:.2f}. "
            f"Due {target.due_date}."
        )
        path = (
            f"/billing/invoices/{target.public_id}"
            if row.audience == "manager"
            else f"/billing?invoice={target.public_id}"
        )
    elif label == "leases.lease":
        if row.target_state and target.status != row.target_state:
            return None
        if row.event == "lease.expiry" and target.status != "active":
            return None
        detail = (
            f"{target.reference}: {target.tenant.full_name}, unit {target.unit.name}. "
            f"Status: {target.get_status_display()}. Lease ends {target.end_date}."
        )
        path = f"/leases/{target.public_id}"
    elif label == "billing.depositdeduction":
        # A withdrawn or since-decided deduction is never announced late.
        if row.target_state and target.status != row.target_state:
            return None
        detail = (
            f"Lease {target.lease.reference}: {target.reason}, {currency} {target.amount:.2f}. "
            f"Status: {target.get_status_display()}. "
            "Nothing is taken from the deposit until the tenant accepts or a dispute is resolved."
            if row.event == "deposit.deduction_proposed"
            else f"Lease {target.lease.reference}: {target.reason}, {currency} "
            f"{target.amount:.2f}. Status: {target.get_status_display()}."
        )
        path = "/leases" if row.audience == "tenant" else f"/leases/{target.lease.public_id}"
    elif label == "billing.depositentry":
        detail = (
            f"Lease {target.lease.reference}: deposit refund of {currency} "
            f"{-target.amount:.2f} recorded"
            + (f", reference {target.reference}" if target.reference else "")
            + f". Paid on {target.occurred_on}."
        )
        path = "/leases" if row.audience == "tenant" else f"/leases/{target.lease.public_id}"
    elif label.startswith("maintenance."):
        job = target.request if label.endswith("maintenanceupdate") else target
        if row.target_state and job.status != row.target_state:
            return None
        detail = f"{job.reference}: {job.title}. Status: {job.get_status_display()}."
        if job.scheduled_for:
            appointment = timezone.localtime(
                job.scheduled_for,
                ZoneInfo(row.organization.timezone),
            )
            detail += f" Scheduled for {appointment:%d %b %Y, %H:%M %Z}."
        if label.endswith("maintenanceupdate"):
            detail += " A new comment is available in Dwella."
        # Public notifications never include internal costs, access notes or comment bodies.
        path = f"/maintenance/{job.public_id}"
    else:
        if row.target_state and target.status != row.target_state:
            return None
        detail = f"{target.reference}: {currency} {target.amount:.2f}."
        if label == "payments.collection":
            detail += f" Invoice {target.invoice.reference}. Payment is not confirmed."
            path = (
                f"/billing/invoices/{target.invoice.public_id}"
                if row.audience == "manager"
                else f"/billing?invoice={target.invoice.public_id}"
            )
        elif label == "payments.payout":
            detail += " The tenant payment remains recorded."
            path = "/billing/payouts"
        else:
            path = "/billing/payouts"
    url = settings.FRONTEND_URL.rstrip("/") + path
    body = f"{row.organization}\n\n{detail}\n\nOpen Dwella: {url}"
    return f"Dwella: {title}", body, url


def _finish(pk, token, **values):
    return OperationalDelivery.objects.filter(
        pk=pk,
        status="sending",
        claim_token=token,
    ).update(**values)


def send_phone(row, subject, body, url, now):
    from apps.audit.runtime_settings import approved_whatsapp_templates, runtime_settings

    pref = NotificationPreferences.objects.filter(user_id=row.recipient_user_id).first()
    if not pref or not getattr(pref, f"{row.channel}_enabled"):
        return "cancelled", "recipient_opted_out", ""
    consents = PhoneMessagingConsent.objects.filter(
        user_id=row.recipient_user_id,
        channel=row.channel,
        allowed=True,
        source="verified_link",
    )
    if not row.recipient_user_id:
        return "held", "verified_phone_required", ""
    if row.audience == "tenant":
        consents = consents.filter(phone=normalize_phone(row.tenant.phone_number))
    consent = consents.order_by("-granted_at", "pk").first()
    if not consent or not phone_allowed(consent.phone):
        return "held", "verified_phone_required", ""
    config = runtime_settings()
    from .messaging import feature_available, quiet_now
    from .models import MessagingSettings

    if not feature_available(row.organization, row.channel):
        return "held", "feature_unavailable", ""
    quiet, created = MessagingSettings.objects.get_or_create(pk=1)
    if created:
        quiet.refresh_from_db()
    if quiet_now(row.organization, quiet, now):
        return "held", "quiet_hours", ""
    if row.channel == "sms":
        if not sms_ready(config):
            return "held", "channel_unavailable", ""
        adapter = SimpleNamespace(recipient=consent.phone, subject=subject, body=body)
        OperationalDelivery.objects.filter(pk=row.pk, claim_token=row.claim_token).update(
            attempts=F("attempts") + 1,
        )
        provider_id = send_sms(adapter, config)
    else:
        if not whatsapp_ready(config):
            return "held", "channel_unavailable", ""
        payload = {"messaging_product": "whatsapp", "to": consent.phone.lstrip("+")}
        if consent.last_inbound_at and consent.last_inbound_at > now - timedelta(hours=24):
            payload.update(type="text", text={"body": f"{subject}\n\n{body}"})
        else:
            template = settings.WHATSAPP_OPERATIONAL_TEMPLATE
            language = config["whatsapp_language"]
            if not template or f"{template}:{language}" not in approved_whatsapp_templates():
                return "held", "operational_template_required", ""
            payload.update(
                type="template",
                template={
                    "name": template,
                    "language": {"code": language},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": subject},
                                {"type": "text", "text": body.split("\n\n")[1]},
                                {"type": "text", "text": url},
                            ],
                        }
                    ],
                },
            )
        OperationalDelivery.objects.filter(pk=row.pk, claim_token=row.claim_token).update(
            attempts=F("attempts") + 1,
        )
        result = post_json(
            f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/"
            f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
            payload,
            {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
        )
        provider_id = result["messages"][0]["id"]
    OperationalDelivery.objects.filter(pk=row.pk).update(recipient=consent.phone)
    return "sent", "provider_accepted", provider_id


def dispatch_operational(*, limit=50, now=None):
    if connection.in_atomic_block:
        raise RuntimeError("Dispatch must run after commit")
    now = now or timezone.now()
    OperationalDelivery.objects.filter(
        status="sending",
        claimed_at__lt=now - timedelta(minutes=10),
    ).update(status="review", reason="send_outcome_unknown")
    OperationalDelivery.objects.filter(
        channel="email", status__in=["queued", "held"],
        created_at__lt=now - timedelta(days=7),
    ).update(status="cancelled", reason="email_expired")
    due = OperationalDelivery.objects.filter(
        status__in=["queued", "held"], available_at__lte=now,
    )
    if not settings.OPERATIONAL_EMAIL_ENABLED:
        due = due.exclude(channel="email")
    ids = list(
        due
        .order_by("available_at", "pk")
        .values_list("pk", flat=True)[: max(1, min(limit, 100))]
    )
    deadline, sent = monotonic() + 45, 0
    for pk in ids:
        if monotonic() >= deadline:
            break
        # Recheck at each send boundary so a pause never consumes pending email.
        if not settings.OPERATIONAL_EMAIL_ENABLED and OperationalDelivery.objects.filter(
            pk=pk, channel="email",
        ).exists():
            continue
        token = uuid.uuid4()
        won = OperationalDelivery.objects.filter(
            pk=pk,
            status__in=["queued", "held"],
            available_at__lte=now,
        ).update(status="sending", claimed_at=now, claim_token=token)
        if not won:
            continue
        row = OperationalDelivery.objects.select_related(
            "organization",
            "recipient_user",
            "tenant",
        ).get(pk=pk)
        if row.event == "invoice.issued" and row.audience == "manager":
            _finish(pk, token, status="cancelled", reason="audience_policy_changed")
            continue
        target = target_for(row)
        if not authorised(row, target):
            _finish(pk, token, status="cancelled", reason="permission_removed")
            continue
        if row.channel != "email" and row.created_at < now - timedelta(days=3):
            _finish(pk, token, status="cancelled", reason="optional_notice_expired")
            continue
        rendered = content(row, target)
        if not rendered:
            _finish(pk, token, status="cancelled", reason="event_superseded")
            continue
        subject, body, url = rendered
        try:
            if row.channel == "email":
                address = row.tenant.email if row.audience == "tenant" else row.recipient_user.email
                if not address or address != row.recipient:
                    _finish(
                        pk,
                        token,
                        status="cancelled",
                        reason="missing_or_changed_email",
                        available_at=now + timedelta(hours=1),
                    )
                    continue
                if not recipient_allowed(address) or not delivery_configured():
                    _finish(
                        pk,
                        token,
                        status="held",
                        reason="delivery_unavailable",
                        available_at=now + timedelta(hours=1),
                    )
                    continue
                OperationalDelivery.objects.filter(pk=pk, claim_token=token).update(
                    attempts=F("attempts") + 1,
                )
                message = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [address])
                message.dwella_bulk = True
                message.extra_headers["Message-ID"] = (
                    f"<dwella-notice-{row.public_id}@{settings.EMAIL_MESSAGE_ID_DOMAIN}>"
                )
                accepted = message.send(fail_silently=False)
                status, reason, provider_id = (
                    ("sent", "transport_accepted", "")
                    if accepted == 1
                    else ("review", "send_outcome_unknown", "")
                )
            else:
                status, reason, provider_id = send_phone(row, subject, body, url, now)
        except EmailQuotaExceeded:
            _finish(
                pk,
                token,
                status="held",
                reason="email_quota_reached",
                available_at=now + timedelta(minutes=15),
            )
        except ProviderRejected as error:
            _finish(pk, token, status="failed", reason=f"provider_rejected:{error.code}"[:80])
        except Exception:
            # Even ordinary SMTP exceptions may occur after DATA acceptance.
            _finish(pk, token, status="review", reason="send_outcome_unknown")
        else:
            _finish(
                pk,
                token,
                status=status,
                reason=reason,
                provider_id=provider_id,
                sent_at=now if status == "sent" else None,
                available_at=now + timedelta(hours=1),
            )
            sent += status == "sent"
    return sent


def schedule_operational(*, limit=100, now=None):
    """Local-day keyset scans, partitioned by timezone; bounded records per tick."""
    now = now or timezone.now()
    zones = list(
        apps.get_model("organizations.Organization").objects.filter(is_active=True)
        .order_by("timezone").values_list("timezone", flat=True).distinct()[:600]
    )
    budget = 2 * max(1, min(limit, 500))
    count = 0
    for zone in zones:
        if budget <= 0:
            break
        try:
            local = now.astimezone(ZoneInfo(zone))
        except (ValueError, ZoneInfoNotFoundError):
            continue
        queued, used = _schedule_zone(zone, local, max(1, min(limit, 500)), budget)
        count += queued
        budget -= used
    return count


def _schedule_zone(zone, local, limit, budget):
    day = local.date()
    count, used = 0, 0
    for source, label in (("invoices", "billing.Invoice"), ("leases", "leases.Lease")):
        if used >= budget:
            break
        size = min(limit, budget - used)
        with transaction.atomic():
            key = f"{source}:{zone}"
            scan, _ = OperationalScan.objects.get_or_create(source=key, defaults={"day": day})
            scan = OperationalScan.objects.select_for_update().get(pk=key)
            if scan.day != day:
                scan.day, scan.after_id, scan.completed = day, 0, False
            if scan.completed:
                continue
            query = (
                apps.get_model(label)
                .objects.filter(
                    is_active=True,
                    organization__is_active=True,
                    organization__timezone=zone,
                    pk__gt=scan.after_id,
                )
                .select_related("organization__reminderpreferences", "tenant__user")
            )
            if source == "invoices":
                query = query.filter(
                    status__in=["open", "partially_paid"],
                    due_date__gte=day - timedelta(days=92),
                    due_date__lte=day + timedelta(days=31),
                )
            else:
                query = query.filter(
                    status="active",
                    end_date__lte=day + timedelta(days=31),
                    end_date__gte=day - timedelta(days=31),
                )
            rows = list(query.order_by("pk")[:size])
            used += len(rows)
            for target in rows:
                try:
                    # A failed insert must roll back this record's partial work,
                    # leaving the scan transaction healthy and its cursor advancing.
                    with transaction.atomic():
                        count += _schedule_target(target, source, local)
                except Exception:
                    logger.exception(
                        "Operational scan skipped source=%s target_id=%s timezone=%s",
                        source, target.pk, zone,
                    )
            scan.after_id = rows[-1].pk if rows else scan.after_id
            scan.completed = len(rows) < size
            scan.save()
    return count, used


def _schedule_target(target, source, local):
    pref = getattr(target.organization, "reminderpreferences", None)
    hour = pref.due_hour if pref else 9
    # Queue future work; a later hour must not block other workspaces.
    deliver_at = local.replace(hour=hour, minute=0, second=0, microsecond=0)
    if source == "invoices":
        from .messaging import reminder_dates

        if not target.tenant.is_active:
            return 0
        if target.due_date not in reminder_dates(
            pref or SimpleNamespace(before_due_days=3, overdue_repeats=3, overdue_every_days=3),
            local.date(),
        ):
            return 0
        enqueue(
            target, "invoice.reminder", suffix=str(local.date()), state=str(local.date()),
            tenant_only=True, optional=False, available_at=deliver_at,
        )
    else:
        days = (target.end_date - local.date()).days
        if days > 30:
            return 0
        milestone = 30 if days > 7 else (7 if days > 0 else 0)
        enqueue(
            target, "lease.expiry", suffix=f"{target.end_date}:{milestone}",
            available_at=deliver_at,
        )
    return 1
