"""Deduction evidence stays private, and deposit changes reach the right people."""

import io
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from reportlab.pdfgen.canvas import Canvas

from apps.notifications.models import OperationalDelivery
from apps.notifications.operational import content, target_for
from apps.organizations.models import Organization
from apps.portal.tests import account

from . import deposits
from .models import DepositEvidence
from .test_deposits import home  # noqa: F401  (shared fixture)
from .tests import make_lease

pytestmark = pytest.mark.django_db
TODAY = timezone.localdate()


def photo(size=(64, 48), orientation=None):
    stream = io.BytesIO()
    image = Image.new("RGB", size, "orange")
    exif = Image.Exif()
    exif[0x010F] = "SecretCam"  # camera maker; must not survive re-encoding
    if orientation:
        exif[0x0112] = orientation
    image.save(stream, "JPEG", exif=exif)
    return SimpleUploadedFile("lock.jpg", stream.getvalue(), content_type="image/jpeg")


def quote_pdf():
    stream = io.BytesIO()
    canvas = Canvas(stream)
    canvas.drawString(72, 720, "Locksmith quote K400")
    canvas.save()
    return SimpleUploadedFile("quote.pdf", stream.getvalue(), content_type="application/pdf")


@pytest.fixture
def deduction(home):  # noqa: F811
    user = home["manager_user"]
    lease = home["lease"]
    deposits.record_opening(lease, amount=Decimal("3000"), occurred_on=TODAY, note="", user=user)
    row = deposits.propose_deduction(
        lease, amount=Decimal("400"), reason="Broken door lock", details="", user=user
    )
    return row


def upload(client, row, file):
    return client.post(
        f"/api/v1/billing/deposit-deductions/{row.public_id}/evidence/", {"file": file}
    )


def test_photo_is_reencoded_without_metadata_and_pdf_is_kept(home, deduction):  # noqa: F811
    manager = home["manager"]
    assert upload(manager, deduction, photo()).status_code == 200
    assert upload(manager, deduction, quote_pdf()).status_code == 200
    image, pdf = DepositEvidence.objects.order_by("created_at")
    assert (image.name, image.content_type) == ("lock.jpg", "image/jpeg")
    assert b"SecretCam" not in bytes(image.content)
    assert b"Exif" not in bytes(image.content)
    assert bytes(pdf.content).startswith(b"%PDF-")
    body = manager.get(f"/api/v1/billing/deposits/{home['lease'].public_id}/").json()
    names = [e["name"] for e in body["response_data"]["deductions"][0]["evidence"]]
    assert names == ["lock.jpg", "quote.pdf"]


def test_full_size_phone_photo_is_kept_upright_and_small(home, deduction):  # noqa: F811
    # 12 MP, stored landscape with "rotate 90" in EXIF, as phones do.
    assert upload(home["manager"], deduction, photo((4000, 3000), orientation=6)).status_code == 200
    stored = Image.open(io.BytesIO(bytes(DepositEvidence.objects.get().content)))
    assert stored.size == (1125, 1500)
    assert DepositEvidence.objects.get().size < 500_000


def test_bad_files_and_too_many_files_are_refused(home, deduction):  # noqa: F811
    manager = home["manager"]
    fake = SimpleUploadedFile("lock.jpg", b"<script>not an image</script>")
    assert upload(manager, deduction, fake).status_code == 400
    broken_pdf = SimpleUploadedFile("quote.pdf", b"%PDF-1.4 broken")
    assert upload(manager, deduction, broken_pdf).status_code == 400
    for _ in range(DepositEvidence.MAX_PER_DEDUCTION):
        assert upload(manager, deduction, photo()).status_code == 200
    assert upload(manager, deduction, photo()).status_code == 400
    assert DepositEvidence.objects.count() == DepositEvidence.MAX_PER_DEDUCTION


def test_only_the_workspace_and_that_tenant_can_open_evidence(home, deduction):  # noqa: F811
    upload(home["manager"], deduction, photo())
    item = DepositEvidence.objects.get()
    manager_url = f"/api/v1/billing/deposit-evidence/{item.public_id}/"
    tenant_url = f"/api/v1/portal/deposit-evidence/{item.public_id}/"
    response = home["manager"].get(manager_url)
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    assert response["Content-Type"] == "image/jpeg"
    assert home["tenant"].get(tenant_url).status_code == 200
    # Another workspace's manager and a neighbouring tenant get nothing.
    other = Organization.objects.create(name="Elsewhere Homes")
    _, outsider = account(other, "landlord", "evidence-outsider")
    assert outsider.get(manager_url).status_code == 404
    neighbour_lease = make_lease(home["org"], unit_name="2B", phone="+260975550000")
    neighbour_user, neighbour = account(home["org"], "tenant", "evidence-neighbour")
    neighbour_lease.tenant.user = neighbour_user
    neighbour_lease.tenant.save(update_fields=["user"])
    assert neighbour.get(tenant_url).status_code == 404
    # A withdrawn deduction's evidence is no longer shown to the tenant.
    deposits.withdraw_deduction(deduction, user=home["manager_user"])
    assert home["tenant"].get(tenant_url).status_code == 404


def test_decided_deduction_takes_no_more_evidence(home, deduction):  # noqa: F811
    deposits.withdraw_deduction(deduction, user=home["manager_user"])
    assert upload(home["manager"], deduction, photo()).status_code == 400


def notices(event):
    return sorted(
        OperationalDelivery.objects.filter(event=event, channel="email").values_list(
            "audience", "recipient"
        )
    )


def test_deposit_changes_notify_the_right_people(home, deduction):  # noqa: F811
    tenant_email = home["lease"].tenant.email
    assert notices("deposit.deduction_proposed") == [("tenant", tenant_email)]
    deposits.respond_to_deduction(deduction, accept=False, note="Wear and tear")
    deposits.respond_to_deduction(deduction, accept=True, note="")
    # Each answer is its own notice to the managers, never to the tenant.
    answered = notices("deposit.deduction_answered")
    assert len(answered) == 2 and {a for a, _ in answered} == {"manager"}
    deposits.apply_deduction(deduction, user=home["manager_user"])
    assert notices("deposit.deduction_applied") == [("tenant", tenant_email)]
    deposits.record_refund(
        home["lease"],
        amount=Decimal("2600"),
        method="bank_transfer",
        reference="FT26",
        paid_on=TODAY,
        note="",
        user=home["manager_user"],
    )
    row = OperationalDelivery.objects.get(event="deposit.refund_recorded", channel="email")
    subject, body, _ = content(row, target_for(row))
    assert subject == "Dwella: Deposit refund recorded"
    assert "2600.00" in body and "FT26" in body


def test_withdrawn_proposal_is_not_announced_late(home, deduction):  # noqa: F811
    deposits.withdraw_deduction(deduction, user=home["manager_user"])
    row = OperationalDelivery.objects.get(event="deposit.deduction_proposed", channel="email")
    assert content(row, target_for(row)) is None
