"""Exact-number consent and direct Meta Cloud API delivery."""

import re
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.common.provider_http import ProviderRejected, post_form, post_json
from apps.tenants.models import Tenant

from .models import PhoneMessagingConsent


def normalize_phone(value):
    value = re.sub(r"[ ()-]", "", str(value or ""))
    if re.fullmatch(r"0[79]\d{8}", value):
        value = "+260" + value[1:]
    elif re.fullmatch(r"260\d{9}", value):
        value = "+" + value
    return value if re.fullmatch(r"\+[1-9]\d{7,14}", value) else ""


def whatsapp_ready():
    return bool(
        settings.WHATSAPP_ENABLED
        and settings.WHATSAPP_ACCESS_TOKEN
        and settings.WHATSAPP_PHONE_NUMBER_ID
        and settings.WHATSAPP_BUSINESS_ACCOUNT_ID
        and settings.WHATSAPP_APP_SECRET
        and settings.WHATSAPP_VERIFY_TOKEN
    )


def sms_ready():
    return bool(
        settings.SMS_ENABLED
        and settings.AFRICASTALKING_USERNAME
        and settings.AFRICASTALKING_API_KEY
        and settings.AFRICASTALKING_SENDER_ID
        and len(settings.AFRICASTALKING_CALLBACK_TOKEN) >= 32
    )


def phone_variants(phone):
    values = [phone, phone[1:]]
    if phone.startswith("+260"):
        values.append("0" + phone[4:])
    return values


def sms_body(row):
    return f"Dwella: {row.subject}\n{row.body}\nOpt out: Dwella Settings > Notifications."


def send_sms(row):
    host = (
        "api.sandbox.africastalking.com"
        if settings.AFRICASTALKING_SANDBOX
        else ("api.africastalking.com")
    )
    result = post_form(
        f"https://{host}/version1/messaging",
        {
            "username": settings.AFRICASTALKING_USERNAME,
            "to": normalize_phone(row.recipient),
            "message": sms_body(row),
            "from": settings.AFRICASTALKING_SENDER_ID,
        },
        {"apiKey": settings.AFRICASTALKING_API_KEY, "Accept": "application/json"},
    )
    recipients = result["SMSMessageData"]["Recipients"]
    if len(recipients) != 1:
        raise ValueError("Unexpected SMS recipients.")
    recipient = recipients[0]
    if normalize_phone(recipient["number"]) != normalize_phone(row.recipient):
        raise ValueError("Unexpected SMS recipient.")
    if recipient.get("statusCode") not in {101, 102}:
        raise ProviderRejected(f"at_{recipient.get('statusCode', 'unknown')}")
    return recipient["messageId"]


def phone_allowed(phone):
    allowed = {normalize_phone(p) for p in settings.OUTBOUND_PHONE_ALLOWLIST}
    if settings.APP_ENVIRONMENT == "test" or allowed:
        return phone in allowed and bool(phone)
    return True


def save_user_consent(user, changes):
    """Only the authenticated tenant can grant consent for their current linked numbers."""
    phones = {
        normalize_phone(p)
        for p in Tenant.objects.filter(user=user, is_active=True).values_list(
            "phone_number", flat=True
        )
    } - {""}
    now = timezone.now()
    for channel in ("sms", "whatsapp"):
        key = f"{channel}_enabled"
        if key not in changes:
            continue
        for phone in sorted(phones):
            defaults = {
                "allowed": changes[key],
                "user": user,
                "source": "tenant_settings",
                "granted_at" if changes[key] else "revoked_at": now,
            }
            PhoneMessagingConsent.objects.update_or_create(
                channel=channel,
                phone=phone,
                defaults=defaults,
            )


def personal_phone_preferences(user, values):
    phones = {
        normalize_phone(p)
        for p in Tenant.objects.filter(user=user, is_active=True).values_list(
            "phone_number", flat=True
        )
    } - {""}
    if not phones:
        return values
    allowed = set(
        PhoneMessagingConsent.objects.filter(
            phone__in=phones,
            allowed=True,
        ).values_list("channel", "phone")
    )
    for channel in ("sms", "whatsapp"):
        values[f"{channel}_enabled"] = values[f"{channel}_enabled"] and all(
            (channel, phone) in allowed for phone in phones
        )
    return values


def phone_block(row, now):
    phone = normalize_phone(row.recipient)
    if not phone:
        return "invalid_phone"
    if not phone_allowed(phone):
        return "recipient_restricted"
    consent = PhoneMessagingConsent.objects.filter(channel=row.channel, phone=phone).first()
    if not consent or not consent.allowed:
        return "recipient_opted_out"
    if row.channel == "whatsapp":
        if row.invoice_id:
            if not settings.WHATSAPP_RENT_TEMPLATE:
                return "whatsapp_template_required"
        elif not consent.last_inbound_at or consent.last_inbound_at <= now - timedelta(hours=24):
            return "whatsapp_reply_window_closed"
    return ""


def whatsapp_rent_parameters(invoice):
    return [
        " ".join(str(value).split()) for value in (
            invoice.tenant.full_name, invoice.organization.name, invoice.reference,
            f"{invoice.organization.currency} {invoice.balance:.2f}",
            invoice.due_date.isoformat(),
        )
    ]


def whatsapp_rent_body(invoice):
    tenant, workspace, reference, balance, due = whatsapp_rent_parameters(invoice)
    return (
        f"Hello {tenant}, {workspace} reminds you that invoice {reference} has {balance} "
        f"outstanding and is due on {due}. Check Dwella for details. "
        "To stop WhatsApp reminders, reply STOP."
    )


def send_whatsapp(row):
    payload = {
        "messaging_product": "whatsapp",
        "to": normalize_phone(row.recipient)[1:],
        "biz_opaque_callback_data": str(row.public_id),
    }
    if row.invoice_id:
        payload.update(
            type="template",
            template={
                "name": settings.WHATSAPP_RENT_TEMPLATE,
                "language": {"code": settings.WHATSAPP_TEMPLATE_LANGUAGE},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(value)}
                            for value in whatsapp_rent_parameters(row.invoice)
                        ],
                    }
                ],
            },
        )
    else:
        payload.update(type="text", text={"body": f"{row.subject}\n\n{row.body}"})
    result = post_json(
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages",
        payload,
        {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
    )
    return result["messages"][0]["id"]
