"""Requested documents, confirmed repair photos and one-invoice reminder journeys."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.billing.models import Invoice
from apps.billing.services import record_payment
from apps.billing.tests import make_lease
from apps.organizations.models import Organization, OrganizationMembership

from . import test_whatsapp as base
from .test_whatsapp import PHONE, choose, step, workspace
from .whatsapp.access import actor_context, revoke
from .whatsapp.documents import available, descriptor, prepare, source
from .whatsapp.models import WhatsAppBinding, WhatsAppReply
from .whatsapp.transport import dispatch_replies

pytestmark = pytest.mark.django_db(transaction=True)
config = base.config
house = base.house


def complete_tenant(house):
    tenant = house["lease"].tenant
    tenant.tpin, tenant.billing_address = "1234567890", "Plot 42, Lusaka"
    tenant.national_id, tenant.identity_country = "123456/12/1", "ZM"
    tenant.save()


def pdf_reply(house, kind="invoice"):
    complete_tenant(house)
    if kind == "statement":
        menu = workspace(house)
        return step(token=choose(menu, "This month statement"))
    if kind == "receipt":
        record_payment(
            invoice=house["invoice"],
            amount=Decimal("100"),
            method="cash",
            paid_on=timezone.localdate(),
            recorded_by=house["manager"],
        )
    menu = workspace(house)
    reply = step(token=choose(menu, "My invoices" if kind == "invoice" else "My receipts"))
    reply = step(token=reply.view["options"][0]["id"])
    return step(token=choose(reply, "Download PDF"))


@pytest.mark.parametrize("kind", ["invoice", "receipt", "statement"])
def test_requested_pdf_is_valid_private_correlated_and_prepared_without_locks(house, kind):
    reply = pdf_reply(house, kind)
    assert reply.view["document"]["kind"] == kind

    def upload(url, raw, content_type, auth):
        assert not connection.in_atomic_block
        assert b"%PDF-" in raw and "multipart/form-data" in content_type
        assert url.endswith("/media") and "Bearer synthetic-access" == auth["Authorization"]
        return {"id": "uploaded-pdf"}

    def send(url, body, auth):
        assert not connection.in_atomic_block
        assert body["type"] == "document" and body["document"]["id"] == "uploaded-pdf"
        assert body["document"]["filename"].endswith(".pdf")
        assert body["biz_opaque_callback_data"] == str(reply.public_id)
        assert body["to"] == PHONE[1:]
        assert "link" not in body["document"]
        return {"messages": [{"id": "wamid.document"}]}

    with (
        patch("apps.notifications.whatsapp.transport.post_request", side_effect=upload),
        patch(
            "apps.notifications.whatsapp.transport.post_json",
            side_effect=send,
        ),
    ):
        assert dispatch_replies() == 1
    reply.refresh_from_db()
    assert reply.status == "sent" and reply.provider_id == "wamid.document"


@pytest.mark.parametrize("change", ["stop", "member", "tenant", "correction", "number", "policy"])
def test_document_access_is_rechecked_after_upload(house, change):
    reply = pdf_reply(house)

    def upload(*args):
        if change == "stop":
            revoke(phone=PHONE)
        elif change == "member":
            OrganizationMembership.objects.filter(user=house["tenant"]).update(is_active=False)
        elif change == "tenant":
            type(house["lease"].tenant).objects.update(user=None)
        elif change == "correction":
            Invoice.objects.filter(pk=house["invoice"].pk).update(amount_paid=Decimal("1"))
        elif change == "number":
            WhatsAppBinding.objects.update(phone="+260971234569")
        else:
            Organization.objects.filter(pk=house["org"].pk).update(is_active=False)
        return {"id": "uploaded-pdf"}

    with (
        patch("apps.notifications.whatsapp.transport.post_request", side_effect=upload),
        patch(
            "apps.notifications.whatsapp.transport.post_json",
        ) as send,
    ):
        assert dispatch_replies() == 0
    send.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == "cancelled"


def test_document_unsafe_or_cross_workspace_descriptors_are_denied(house):
    workspace(house)
    ctx = actor_context(WhatsAppBinding.objects.get(), house["org"].pk)
    other = make_lease(Organization.objects.create(name="Other"))
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
    assert not available(ctx, descriptor("invoice", foreign.public_id, house["org"]))
    assert not available(ctx, {"kind": "receipt", "target": "bad-uuid"})
    assert not available(ctx, {"kind": "file", "target": str(house["invoice"].public_id)})
    assert not available(ctx, None)
    with pytest.raises(PermissionDenied):
        source(ctx, descriptor("invoice", foreign.public_id, house["org"]))


def test_incomplete_invoice_and_large_statement_fall_back_to_authenticated_web(house):
    reply = pdf_reply(house)
    type(house["lease"].tenant).objects.update(tpin="")
    with (
        patch("apps.notifications.whatsapp.transport.post_request") as upload,
        patch(
            "apps.notifications.whatsapp.transport.post_json",
            return_value={"messages": [{"id": "wamid.fallback"}]},
        ) as send,
    ):
        assert dispatch_replies() == 1
    upload.assert_not_called()
    assert send.call_args.args[1]["type"] == "text"
    body = send.call_args.args[1]["text"]["body"]
    assert "invoice PDF needs complete tenant details: TPIN" in body
    assert "Ask your property manager" in send.call_args.args[1]["text"]["body"]
    assert str(house["invoice"].public_id) in send.call_args.args[1]["text"]["body"]
    reply.refresh_from_db()
    assert reply.status == "sent"


def test_uncertain_document_send_is_not_retried(house):
    reply = pdf_reply(house)
    with (
        patch("apps.notifications.whatsapp.transport.post_request", return_value={"id": "upload"}),
        patch(
            "apps.notifications.whatsapp.transport.post_json",
            side_effect=TimeoutError,
        ) as send,
    ):
        assert dispatch_replies() == 0
        assert dispatch_replies() == 0
    assert send.call_count == 1
    reply.refresh_from_db()
    assert (reply.status, reply.reason) == ("review", "send_outcome_unknown")


def test_pdf_request_limit_and_bound_statement_rows(house):
    reply = pdf_reply(house, "statement")
    for number in range(11):
        inbound = base.WhatsAppInbound.objects.create(
            number_id="number-id",
            provider_id=f"pdf-limit-{number}",
            phone=PHONE,
            happened_at=timezone.now(),
        )
        WhatsAppReply.objects.create(inbound=inbound, binding=reply.binding, view=reply.view)
    assert "limit reached" in step("statement").view["text"]
    ctx = actor_context(reply.binding, house["org"].pk)
    with (
        patch("apps.notifications.whatsapp.documents.MAX_EVENTS", 0),
        pytest.raises(ValidationError),
    ):
        prepare(ctx, reply.view["document"])


def test_statement_reads_are_constant_with_small_and_full_documents(house):
    reply = pdf_reply(house, "statement")
    ctx = actor_context(reply.binding, house["org"].pk)
    doc = reply.view["document"]
    with CaptureQueriesContext(connection) as small:
        data = source(ctx, doc)
    assert data["closing"] == str(house["invoice"].total)
    template = house["invoice"]
    Invoice.objects.bulk_create(
        [
            Invoice(
                organization=house["org"],
                tenant=template.tenant,
                unit=template.unit,
                reference=f"WA-PDF-{index}",
                issue_date=timezone.localdate(),
                due_date=timezone.localdate(),
                total="1.00",
                status="open",
            )
            for index in range(49)
        ]
    )
    with CaptureQueriesContext(connection) as full:
        data = source(ctx, doc)
    assert len(data["rows"]) == 50 and len(small) == len(full)
    print(f"WhatsApp statement PDF source queries small={len(small)}, full={len(full)}")


@pytest.mark.parametrize("kind", ["invoice", "receipt"])
def test_invoice_and_receipt_reads_do_not_query_once_per_payment(house, kind):
    from apps.billing.models import Payment

    reply = pdf_reply(house, kind)
    ctx = actor_context(reply.binding, house["org"].pk)
    with CaptureQueriesContext(connection) as small:
        source(ctx, reply.view["document"])
    Payment.objects.bulk_create(
        [
            Payment(
                organization=house["org"],
                invoice=house["invoice"],
                tenant=house["lease"].tenant,
                receipt_number=f"WA-RECEIPT-{index}",
                amount="1.00",
                method="cash",
                paid_on=timezone.localdate(),
            )
            for index in range(49)
        ]
    )
    with CaptureQueriesContext(connection) as full:
        source(ctx, reply.view["document"])
    assert len(small) == len(full)
    print(f"WhatsApp {kind} PDF source queries small={len(small)}, full={len(full)}")
