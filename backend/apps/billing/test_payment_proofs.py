"""Tenants report direct payments; nothing changes until a manager confirms."""

# ruff: noqa: F811
import io
from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from apps.audit.models import AuditEvent
from apps.notifications.models import OperationalDelivery
from apps.portal.tests import account, data

from .models import Invoice, Payment, PaymentProof
from .services import create_invoice, record_payment
from .test_deposits import home  # noqa: F401  (shared fixture)
from .tests import make_lease

pytestmark = pytest.mark.django_db
TODAY = timezone.localdate()
D = Decimal
PORTAL = "/api/v1/portal/payment-proofs/"
BILLING = "/api/v1/billing/payment-proofs/"


def screenshot(name="mtn.png", colour="white"):
    raw = io.BytesIO()
    Image.new("RGB", (8, 8), colour).save(raw, format="PNG")
    return SimpleUploadedFile(name, raw.getvalue(), content_type="image/png")


def rent(lease, amount="3900"):
    return create_invoice(
        organization=lease.organization,
        tenant=lease.tenant,
        lease=lease,
        issue_date=TODAY,
        due_date=TODAY,
        lines=[{"kind": "rent", "description": "Rent", "amount": D(amount)}],
    )


def submit(client, invoice, files=None, **fields):
    body = {
        "invoice": str(invoice.public_id),
        "amount": "3900",
        "method": "mobile_money",
        "paid_on": TODAY.isoformat(),
        "reference": "MP241101.1234",
        **fields,
    }
    if files is not None:
        body["files"] = files
    return client.post(PORTAL, body, format="multipart")


def test_proof_changes_nothing_until_the_manager_confirms(home):
    invoice = rent(home["lease"])
    response = submit(home["tenant"], invoice, files=[screenshot()])
    assert response.status_code == 201, response.content
    body = data(response)
    assert body["status"] == "submitted" and body["number"] == "PRF-0001"
    assert len(body["files"]) == 1 and body["files"][0]["content_type"] == "image/jpeg"
    invoice.refresh_from_db()
    assert invoice.amount_paid == 0 and not Payment.objects.exists()
    assert OperationalDelivery.objects.filter(event="proof.submitted", audience="manager").exists()
    assert AuditEvent.objects.filter(action="payment_proof.submitted").exists()

    detail = data(home["manager"].get(f"/api/v1/billing/invoices/{invoice.public_id}/"))
    assert [row["number"] for row in detail["pending_proofs"]] == ["PRF-0001"]
    listing = data(home["manager"].get(f"{BILLING}?status=open"))
    assert listing["waiting"] == 1 and listing["results"][0]["can_review"] is True
    proof = PaymentProof.objects.get()
    confirmed = data(home["manager"].post(f"{BILLING}{proof.public_id}/confirm/"))
    assert confirmed["status"] == "confirmed" and confirmed["receipt"]["number"].startswith("RCT-")
    payment = Payment.objects.get()
    assert (payment.amount, payment.method, payment.reference) == (
        D("3900"),
        "mobile_money",
        "MP241101.1234",
    )
    assert payment.recorded_by == home["manager_user"]
    invoice.refresh_from_db()
    assert invoice.status == Invoice.Status.PAID
    # A second click (or an old WhatsApp button) does not record it twice.
    again = home["manager"].post(f"{BILLING}{proof.public_id}/confirm/")
    assert again.status_code == 200 and Payment.objects.count() == 1


@pytest.mark.parametrize(
    "fields, field",
    [
        ({"amount": "5000"}, "amount"),
        ({"paid_on": (TODAY + timedelta(days=1)).isoformat()}, "paid_on"),
        ({"method": "card"}, "method"),
        ({"reference": ""}, "files"),
    ],
)
def test_bad_reports_are_refused(home, fields, field):
    invoice = rent(home["lease"])
    response = submit(home["tenant"], invoice, **fields)
    assert response.status_code == 400 and field in data(response), response.content
    assert not PaymentProof.objects.exists()


def test_tenants_only_reach_their_own_invoices_and_proofs(home):
    from apps.organizations.models import Organization

    other_org = Organization.objects.create(name="Other Lets")
    stranger_invoice = rent(make_lease(other_org, unit_name="9Z", phone="+260974000999"))
    assert submit(home["tenant"], stranger_invoice).status_code == 404
    own = rent(home["lease"])
    data(submit(home["tenant"], own, files=[screenshot()]))
    proof = PaymentProof.objects.get()
    _, outsider = account(other_org, "landlord", "other-manager")
    assert outsider.get(f"{BILLING}{proof.public_id}/").status_code == 404
    file_id = proof.files.get().public_id
    assert outsider.get(f"/api/v1/billing/payment-proof-files/{file_id}/").status_code == 404
    opened = home["tenant"].get(f"/api/v1/portal/payment-proof-files/{file_id}/")
    assert opened.status_code == 200 and opened["Cache-Control"] == "private, no-store"


def test_question_resend_then_not_received(home):
    invoice = rent(home["lease"])
    data(submit(home["tenant"], invoice, files=[screenshot()]))
    proof = PaymentProof.objects.get()
    manager = home["manager"]
    assert manager.post(f"{BILLING}{proof.public_id}/ask/", {"note": ""}).status_code == 400
    asked = data(manager.post(f"{BILLING}{proof.public_id}/ask/", {"note": "Which number?"}))
    assert asked["status"] == "needs_information"
    assert OperationalDelivery.objects.filter(event="proof.needs_information").exists()
    # Confirming needs a fresh submission.
    assert manager.post(f"{BILLING}{proof.public_id}/confirm/").status_code == 400

    resent = home["tenant"].post(
        f"{PORTAL}{proof.public_id}/resend/",
        {
            "amount": "3900",
            "method": "mobile_money",
            "paid_on": TODAY.isoformat(),
            "reference": "MP241101.9999",
            "note": "Paid from 0977 000 111",
        },
        format="multipart",
    )
    body = data(resent)
    assert body["status"] == "submitted" and body["revision"] == 2
    assert body["history"][0]["reference"] == "MP241101.1234"
    assert body["history"][0]["question"] == "Which number?"

    refused = data(manager.post(f"{BILLING}{proof.public_id}/reject/", {"note": "Not in MTN"}))
    assert refused["status"] == "rejected"
    assert OperationalDelivery.objects.filter(event="proof.rejected", audience="tenant").exists()
    assert not Payment.objects.exists()


def test_confirming_after_the_balance_changed_is_refused(home):
    invoice = rent(home["lease"])
    data(submit(home["tenant"], invoice, files=[screenshot()]))
    record_payment(invoice=invoice, amount=D("1000"), method="cash", paid_on=TODAY)
    proof = PaymentProof.objects.get()
    response = home["manager"].post(f"{BILLING}{proof.public_id}/confirm/")
    assert response.status_code == 400 and "2900.00" in str(data(response))
    proof.refresh_from_db()
    assert proof.status == "submitted" and Payment.objects.count() == 1


def test_same_screenshot_twice_is_flagged_and_tenant_can_cancel(home):
    invoice = rent(home["lease"], "8000")
    data(submit(home["tenant"], invoice, files=[screenshot()], amount="3900"))
    second = data(submit(home["tenant"], invoice, files=[screenshot()], amount="3900"))
    detail = data(home["manager"].get(f"{BILLING}{second['id']}/"))
    assert detail["possible_duplicates"] == ["PRF-0001"]
    cancelled = data(home["tenant"].post(f"{PORTAL}{second['id']}/cancel/"))
    assert cancelled["status"] == "cancelled" and cancelled["can_cancel"] is False
    assert data(home["manager"].get(f"{BILLING}?status=open"))["waiting"] == 1


def test_manager_list_queries_do_not_grow_with_proofs(home, django_assert_max_num_queries):
    invoice = rent(home["lease"], "50000")
    for colour in ("white", "red", "blue", "green", "black", "gray"):
        data(submit(home["tenant"], invoice, files=[screenshot(colour=colour)], amount="100"))
        PaymentProof.objects.filter(status="submitted").update(status="cancelled")
    # Session, workspace, count, proofs, files, duplicate check: fixed, whatever the count.
    with django_assert_max_num_queries(8):
        body = data(home["manager"].get(BILLING))
    assert len(body["results"]) == 6
