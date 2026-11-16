"""Private, bounded invoice/receipt copies for an already-authorized notice."""

from types import SimpleNamespace

from django.conf import settings
from django.db import connection
from rest_framework.exceptions import APIException

from apps.audit.provider_credentials import credential
from apps.common.provider_http import post_request

from .phone_messaging import normalize_phone
from .whatsapp import documents
from .whatsapp.evidence import _multipart

TEMPLATES = {
    "invoice.issued": "dwella_invoice_document",
    "payment.confirmed": "dwella_receipt_document",
}


def kind(row):
    if not settings.NOTIFICATION_DOCUMENTS_ENABLED:
        return None
    return {
        ("invoice.issued", "billing.invoice"): "invoice",
        ("payment.confirmed", "billing.payment"): "receipt",
    }.get((row.event, row.target_model))


def context(row, target):
    # The caller authorizes this exact notice and recipient. The shared PDF reader
    # may then read only this target, never a workspace-wide synthetic permission.
    return SimpleNamespace(
        organization=row.organization,
        role=row.audience,
        tenant_ids=[row.tenant_id],
        scope=lambda query: query.filter(organization_id=row.organization_id, pk=target.pk),
    )


def prepare(row, target):
    document = documents.descriptor(kind(row), target.public_id, row.organization)
    item, expected = documents.prepare(context(row, target), document)
    return item, document, expected


def current(row, document, expected, *, phone=None):
    from .models import NotificationPreferences, OperationalDelivery, PhoneMessagingConsent
    from .operational import authorised, content, target_for

    fresh = OperationalDelivery.objects.select_related(
        "organization", "recipient_user", "tenant",
    ).get(pk=row.pk)
    target = target_for(fresh)
    if not authorised(fresh, target) or not content(fresh, target):
        return False
    if fresh.channel == "email":
        address = fresh.tenant.email if fresh.audience == "tenant" else fresh.recipient_user.email
        if not address or address != row.recipient:
            return False
    if phone is not None:
        if fresh.audience == "tenant" and normalize_phone(fresh.tenant.phone_number) != phone:
            return False
        if not NotificationPreferences.objects.filter(
            user_id=fresh.recipient_user_id, whatsapp_enabled=True,
        ).exists() or not PhoneMessagingConsent.objects.filter(
            channel="whatsapp", user_id=fresh.recipient_user_id, phone=phone,
            allowed=True, revoked_at__isnull=True, source="verified_link",
        ).exists():
            return False
    try:
        return documents.current(context(fresh, target), document, expected)
    except APIException:
        return False


def template(row, target):
    from .money_templates import money_template

    dedicated = money_template(row, target)
    if dedicated:
        return TEMPLATES[row.event], dedicated[1]
    # Managers receive the same receipt, addressed to their own account.
    values = (
        row.recipient_user.get_full_name() or "there", row.organization.name,
        f"{row.organization.currency} {target.amount:,.2f}", target.invoice.reference,
    )
    return TEMPLATES[row.event], [" ".join(str(value).split()) for value in values]


def upload(item):
    if connection.in_atomic_block:
        raise RuntimeError("Document uploads must run outside a transaction.")
    body, content_type = _multipart(
        {"messaging_product": "whatsapp", "type": item.content_type}, item,
    )
    media = post_request(
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/media",
        body, content_type, {"Authorization": f"Bearer {credential('WHATSAPP_ACCESS_TOKEN')}"},
    )["id"]
    if not isinstance(media, str) or not media or len(media) > 160:
        raise ValueError("Invalid uploaded media identity.")
    return media
