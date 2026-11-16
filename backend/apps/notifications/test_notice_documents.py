from datetime import timedelta
from unittest.mock import patch

import pypdfium2 as pdfium
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.billing.models import Invoice, InvoiceLine, Payment
from apps.organizations.models import OrganizationMembership

from . import test_operational as base
from .models import NotificationPreferences, OperationalDelivery, PhoneMessagingConsent
from .operational import dispatch_operational, enqueue

pytestmark = pytest.mark.django_db(transaction=True)
house = base.house


@pytest.fixture(autouse=True)
def documents_enabled(settings):
    settings.NOTIFICATION_DOCUMENTS_ENABLED = True


def text(raw):
    with pdfium.PdfDocument(raw) as pdf:
        return "\n".join(page.get_textpage().get_text_range() for page in pdf)


@pytest.mark.parametrize("event", ["invoice.issued", "payment.confirmed"])
def test_email_contains_the_actual_pdf_once(house, mailoutbox, event):
    target = house[4] if event == "invoice.issued" else base.paid(house)
    enqueue(target, event)
    expected = 1 if event == "invoice.issued" else 2
    assert dispatch_operational() == expected
    assert len(mailoutbox) == expected
    for message in mailoutbox:
        filename, content, mimetype = message.attachments[0]
        assert filename.endswith(".pdf") and mimetype == "application/pdf"
        assert content.startswith(b"%PDF-")
        reference = target.reference if event == "invoice.issued" else target.receipt_number
        assert reference in text(content)
    assert dispatch_operational() == 0


def test_missing_invoice_details_has_a_truthful_link_fallback(house, mailoutbox):
    tenant = house[3].tenant
    tenant.tpin = ""
    tenant.save()
    enqueue(house[4], "invoice.issued")
    assert dispatch_operational() == 1
    message = mailoutbox[0]
    assert not message.attachments
    assert "PDF could not be attached" in message.body
    assert "PDF could not be attached" in message.alternatives[0][0]


def test_email_rechecks_recipient_after_rendering(house, mailoutbox):
    from .notice_documents import prepare

    enqueue(house[4], "invoice.issued")

    def render_then_change(*args):
        result = prepare(*args)
        house[3].tenant.__class__.objects.filter(pk=house[3].tenant_id).update(email="new@example.com")
        return result

    with patch("apps.notifications.notice_documents.prepare", side_effect=render_then_change):
        assert dispatch_operational() == 0
    assert not mailoutbox
    assert OperationalDelivery.objects.get().reason == "document_or_access_changed"


def whatsapp(house, settings, event="payment.confirmed", *, active=True, manager=False):
    settings.WHATSAPP_ENABLED = True
    settings.WHATSAPP_ACCESS_TOKEN = "synthetic-access"
    settings.WHATSAPP_APP_SECRET = "synthetic-secret"
    settings.WHATSAPP_VERIFY_TOKEN = "synthetic-verify"
    settings.WHATSAPP_PHONE_NUMBER_ID = "synthetic-number"
    settings.WHATSAPP_BUSINESS_ACCOUNT_ID = "synthetic-account"
    user = house[1] if manager else house[2]
    phone = "+260971234567" if manager else house[3].tenant.phone_number
    settings.OUTBOUND_PHONE_ALLOWLIST = [phone]
    NotificationPreferences.objects.create(user=user, whatsapp_enabled=True)
    PhoneMessagingConsent.objects.create(
        user=user, phone=phone, channel="whatsapp", source="verified_link", allowed=True,
        last_inbound_at=timezone.now() - timedelta(hours=1 if active else 25),
    )
    target = house[4] if event == "invoice.issued" else base.paid(house)
    enqueue(target, event)
    OperationalDelivery.objects.exclude(channel="whatsapp").delete()
    assert OperationalDelivery.objects.count() == 1
    return target


@pytest.mark.parametrize("event", ["invoice.issued", "payment.confirmed"])
def test_whatsapp_uploads_a_pdf_and_sends_one_document(house, settings, event):
    whatsapp(house, settings, event)

    def upload(url, raw, content_type, auth):
        assert not connection.in_atomic_block
        assert url.endswith("/media") and b"%PDF-" in raw
        assert "multipart/form-data" in content_type
        return {"id": "private-pdf-id"}

    with (
        patch("apps.notifications.messaging.quiet_now", return_value=False),
        patch("apps.notifications.notice_documents.post_request", side_effect=upload) as media,
        patch("apps.notifications.operational.post_json",
              return_value={"messages": [{"id": "notice-with-pdf"}]}) as send,
    ):
        assert dispatch_operational() == 1
        assert dispatch_operational() == 0
    assert media.call_count == send.call_count == 1
    payload = send.call_args.args[1]
    assert payload["type"] == "document"
    assert payload["document"]["id"] == "private-pdf-id"
    assert "https://" not in str(payload["document"].get("link", ""))


@pytest.mark.parametrize("manager", [False, True])
def test_outside_chat_uses_approved_document_header(house, settings, manager):
    whatsapp(house, settings, active=False, manager=manager)
    settings.APPROVED_WHATSAPP_TEMPLATES = ["dwella_receipt_document:en"]
    with (
        patch("apps.notifications.messaging.quiet_now", return_value=False),
        patch("apps.notifications.notice_documents.upload", return_value="private-media"),
        patch("apps.notifications.operational.post_json",
              return_value={"messages": [{"id": "template-pdf"}]}) as send,
    ):
        assert dispatch_operational() == 1
    template = send.call_args.args[1]["template"]
    assert template["name"] == "dwella_receipt_document"
    assert template["components"][0]["parameters"][0]["document"]["id"] == "private-media"


def test_unapproved_document_template_keeps_existing_notice_without_upload(house, settings):
    whatsapp(house, settings, active=False)
    settings.APPROVED_WHATSAPP_TEMPLATES = ["dwella_payment_received:en"]
    with (
        patch("apps.notifications.messaging.quiet_now", return_value=False),
        patch("apps.notifications.notice_documents.upload") as upload,
        patch("apps.notifications.operational.post_json",
              return_value={"messages": [{"id": "existing-template"}]}) as send,
    ):
        assert dispatch_operational() == 1
    upload.assert_not_called()
    assert send.call_count == 1
    assert send.call_args.args[1]["template"]["name"] == "dwella_payment_received"


@pytest.mark.parametrize("change", ["stop", "preferences", "role", "reverse", "void", "pause"])
def test_change_during_upload_never_discloses_document(house, settings, change):
    payment = whatsapp(house, settings, manager=True)

    def upload(_item):
        if change == "stop":
            PhoneMessagingConsent.objects.update(allowed=False, revoked_at=timezone.now())
        elif change == "preferences":
            NotificationPreferences.objects.update(whatsapp_enabled=False)
        elif change == "role":
            OrganizationMembership.objects.filter(user=house[1]).update(is_active=False)
        elif change == "reverse":
            Payment.objects.filter(pk=payment.pk).update(reversed_at=timezone.now())
        elif change == "void":
            Invoice.objects.filter(pk=house[4].pk).update(status="void")
        else:
            settings.WHATSAPP_ENABLED = False
        return "uploaded-but-not-sent"

    with (
        patch("apps.notifications.messaging.quiet_now", return_value=False),
        patch("apps.notifications.notice_documents.upload", side_effect=upload),
        patch("apps.notifications.operational.post_json") as send,
    ):
        assert dispatch_operational() == 0
    send.assert_not_called()
    assert OperationalDelivery.objects.get().status == "cancelled"


def test_chat_window_closing_during_upload_uses_existing_template(house, settings):
    whatsapp(house, settings)
    settings.APPROVED_WHATSAPP_TEMPLATES = ["dwella_payment_received:en"]

    def upload(_):
        PhoneMessagingConsent.objects.update(last_inbound_at=timezone.now() - timedelta(hours=25))
        return "unused-media"

    with (
        patch("apps.notifications.messaging.quiet_now", return_value=False),
        patch("apps.notifications.notice_documents.upload", side_effect=upload),
        patch("apps.notifications.operational.post_json",
              return_value={"messages": [{"id": "fallback-template"}]}) as send,
    ):
        assert dispatch_operational() == 1
    assert send.call_args.args[1]["type"] == "template"
    assert "unused-media" not in str(send.call_args)


def test_invoice_pdf_query_count_does_not_grow_per_line(house):
    from .notice_documents import prepare

    invoice = house[4]
    enqueue(invoice, "invoice.issued")
    row = OperationalDelivery.objects.select_related("organization", "tenant").get()
    with CaptureQueriesContext(connection) as small:
        prepare(row, invoice)
    InvoiceLine.objects.bulk_create([
        InvoiceLine(invoice=invoice, kind="rent", description=f"Charge {n}", amount=1)
        for n in range(99)
    ])
    Invoice.objects.filter(pk=invoice.pk).update(total=199)
    with CaptureQueriesContext(connection) as full:
        prepare(row, invoice)
    assert len(small) == len(full)
    assert len(full) <= 12
