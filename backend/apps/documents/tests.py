import io
import re
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image, ImageDraw
from rest_framework.test import APIClient

from apps.billing.models import Invoice
from apps.billing.services import generate_rent_invoices
from apps.billing.tests import make_lease
from apps.organizations.models import Organization, OrganizationMembership

from .files import inspect_pdf
from .models import DocumentVersion, SignedLeaseOriginal, SigningInvite
from .rendering import digest

ROOT = "/api/v1/documents/versions/"
pytestmark = pytest.mark.django_db


def member(org, name="manager", role="landlord"):
    user = get_user_model().objects.create_user(
        username=name, email=f"{name}@example.com", first_name=name.title()
    )
    OrganizationMembership.objects.create(organization=org, user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)
    return user, client


@pytest.fixture(autouse=True)
def isolated_mail_and_throttles(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def setup():
    org = Organization.objects.create(name="Kafue Ridge Properties")
    user, client = member(org)
    lease = make_lease(org, active=False)
    lease.tenant.email = "tenant@example.com"
    lease.tenant.save()
    return org, user, client, lease


def prepare(setup, **overrides):
    org, user, client, lease = setup
    payload = {
        "lease": str(lease.public_id),
        "landlord_name": org.name,
        "landlord_address": "Plot 24, Lusaka, Zambia",
        "agreement_text": "Approved complete agreement wording. " * 20,
        "schedule_text": "Inventory: two keys.",
        "terms_approved": True,
    }
    response = client.post(ROOT, {**payload, **overrides}, format="json")
    assert response.status_code == 201, response.content
    return response.json()["response_data"]


def png(blank=False):
    image = Image.new("RGB", (400, 140), "white")
    if not blank:
        ImageDraw.Draw(image).line(
            [(15, 90), (80, 35), (120, 100), (320, 50)], fill="black", width=4
        )
    stream = io.BytesIO()
    image.save(stream, "PNG")
    return SimpleUploadedFile("signature.png", stream.getvalue(), content_type="image/png")


def sign_payload(doc, name="Manager", **extra):
    return {
        "expected_sha256": doc["sha256"],
        "signer_name": name,
        "signature": png(),
        "source": "drawn",
        "consent": True,
        **extra,
    }


def invitation(client, doc):
    response = client.post(f"{ROOT}{doc['id']}/invite/", {}, format="json")
    assert response.status_code == 200, response.content
    token = response.json()["response_data"]["url"].rsplit("/", 1)[1]
    return token, f"/api/v1/signing/{token}/"


def verified(client, doc):
    token, url = invitation(client, doc)
    public = APIClient()
    assert public.post(url + "request-code/").status_code == 200
    code = re.search(r"code is (\d{6})", mail.outbox[-1].body)[1]
    response = public.post(url + "verify/", {"code": code}, format="json")
    assert response.status_code == 200, response.content
    session = response.json()["response_data"]["session"]
    public.credentials(HTTP_X_DWELLA_SIGNING_SESSION=session)
    return public, token, url


def test_pdf_versions_preview_and_no_page_restructure(setup):
    _, _, client, lease = setup
    doc = prepare(setup)
    record = DocumentVersion.objects.get()
    assert record.page_count >= 2
    assert bytes(record.pdf).startswith(b"%PDF-")
    assert digest(bytes(record.pdf)) == doc["sha256"]
    info = inspect_pdf(bytes(record.pdf))
    assert info["pages"] == record.page_count
    url = f"{ROOT}{doc['id']}/"
    preview = client.get(url + f"page/?page=1&sha256={doc['sha256']}")
    assert preview.status_code == 200, preview.content
    assert preview.content.startswith(b"\x89PNG")
    assert preview["Cache-Control"] == "private, no-store"
    assert client.get(url + "page/?page=1&sha256=old").status_code == 400
    second = prepare(setup)
    record.refresh_from_db()
    assert record.status == "superseded" and second["version"] == 2
    assert bytes(record.pdf) == bytes(record.unsigned_pdf)
    lease.refresh_from_db()
    assert lease.status == "draft"


def test_rendered_pages_are_reused_without_a_worker_or_render_throttle(setup):
    _, _, client, _ = setup
    doc = prepare(setup)
    url = f"{ROOT}{doc['id']}/page/?page=1&sha256={doc['sha256']}"
    first = client.get(url)
    assert first.status_code == 200, first.content
    with (
        patch("apps.documents.views.inspect_pdf") as worker,
        patch("apps.documents.throttles.DocumentRenderThrottle.rate", "1/hour"),
    ):
        for _ in range(3):
            again = client.get(url)
            assert again.status_code == 200
            assert again.content == first.content
            assert again["Cache-Control"] == "private, no-store"
    worker.assert_not_called()
    # A cached digest never bypasses the version check.
    assert client.get(f"{ROOT}{doc['id']}/page/?page=1&sha256={'0' * 64}").status_code == 400


def test_invoice_preview_on_a_later_day_reuses_the_unchanged_version(setup):
    org, _, client, lease = setup
    lease.status = "active"
    lease.save()
    generate_rent_invoices(org, timezone.localdate().replace(day=1))
    invoice = Invoice.objects.get()
    url = f"/api/v1/billing/invoices/{invoice.public_id}/document/"
    doc = client.post(url).json()["response_data"]
    later = timezone.localdate() + timedelta(days=3)
    with patch("django.utils.timezone.localdate", return_value=later):
        again = client.post(url).json()["response_data"]
    assert again["id"] == doc["id"]
    assert DocumentVersion.objects.filter(invoice=invoice).count() == 1


def test_invoice_snapshot_is_private_immutable_and_deduplicated(setup):
    org, _, client, lease = setup
    lease.status = "active"
    lease.save()
    generate_rent_invoices(org, timezone.localdate().replace(day=1))
    invoice = Invoice.objects.get()
    url = f"/api/v1/billing/invoices/{invoice.public_id}/document/"
    response = client.post(url)
    assert response.status_code == 200, response.content
    doc = response.json()["response_data"]
    assert doc["kind"] == "invoice"
    assert client.post(url).json()["response_data"]["id"] == doc["id"]
    original = bytes(DocumentVersion.objects.get().pdf)
    invoice.tenant.full_name = "Changed name"
    invoice.tenant.save()
    assert client.post(url).json()["response_data"]["version"] == 2
    assert bytes(DocumentVersion.objects.get(public_id=doc["id"]).pdf) == original
    assert APIClient().get(f"{ROOT}{doc['id']}/pdf/").status_code == 403


def test_complete_two_party_signing_preserves_revisions_and_does_not_activate(
    setup, django_capture_on_commit_callbacks
):
    _, _, client, lease = setup
    doc = prepare(setup)
    public, _, url = verified(client, doc)
    before = bytes(DocumentVersion.objects.get().pdf)
    landlord = client.post(f"{ROOT}{doc['id']}/sign/", sign_payload(doc))
    assert landlord.status_code == 200, landlord.content
    first = landlord.json()["response_data"]
    assert first["sha256"] != doc["sha256"]
    stale = public.post(url + "sign/", sign_payload(doc, lease.tenant.full_name))
    assert stale.status_code == 400
    with django_capture_on_commit_callbacks(execute=True):
        tenant = public.post(url + "sign/", sign_payload(first, lease.tenant.full_name))
    assert tenant.status_code == 200, tenant.content
    final = tenant.json()["response_data"]
    assert final["status"] == "signed"
    record = DocumentVersion.objects.get()
    assert bytes(record.unsigned_pdf) == before
    assert record.signatures.count() == 2
    assert record.copies_emailed_at and not record.delivery_failed
    assert mail.outbox[-1].attachments[0][1] == bytes(record.pdf)
    assert record.signatures.first().reviewed_sha256 == doc["sha256"]
    assert record.signatures.first().sha256 == first["sha256"]
    assert public.get(url + "pdf/").status_code == 200
    assert (
        public.post(url + "sign/", sign_payload(final, lease.tenant.full_name)).status_code == 403
    )
    assert client.post(f"{ROOT}{doc['id']}/revoke/").status_code == 400
    lease.refresh_from_db()
    assert lease.status == "draft"
    assert client.delete(f"/api/v1/leases/{lease.public_id}/").status_code == 400


@pytest.mark.parametrize("change", ["consent", "name", "blank", "malformed", "digest"])
def test_signature_validation_and_rollback(setup, change):
    doc = prepare(setup)
    payload = sign_payload(doc)
    updates = {
        "consent": {"consent": False},
        "name": {"signer_name": "Someone else"},
        "blank": {"signature": png(blank=True)},
        "malformed": {"signature": SimpleUploadedFile("bad.png", b"not an image")},
        "digest": {"expected_sha256": "a" * 64},
    }
    payload.update(updates[change])
    response = setup[2].post(f"{ROOT}{doc['id']}/sign/", payload)
    assert response.status_code == 400, response.content
    record = DocumentVersion.objects.get()
    assert not record.signatures.exists() and record.sha256 == doc["sha256"]


def test_authority_tenant_and_organization_boundaries(setup):
    org, _, client, _ = setup
    doc = prepare(setup)
    _, peer = member(org, "peer")
    _, tenant = member(org, "tenant", "tenant")
    _, foreign = member(Organization.objects.create(name="Elsewhere"), "other")
    url = f"{ROOT}{doc['id']}/"
    assert peer.post(url + "sign/", sign_payload(doc)).status_code == 403
    assert tenant.get(url).status_code == 403
    assert tenant.post(url + "sign/", sign_payload(doc)).status_code == 403
    assert foreign.get(url).status_code == 404
    assert foreign.post(url + "invite/").status_code == 404
    assert APIClient().get(url).status_code == 403
    assert client.patch(url, {"snapshot": {}}, format="json").status_code == 405
    assert client.delete(url).status_code == 405
    staff, _ = member(org, "support")
    staff.is_staff = True
    staff.save()
    bad = client.post(
        ROOT,
        {
            "lease": str(setup[3].public_id),
            "landlord_name": "Owner",
            "landlord_address": "Lusaka",
            "landlord_signer": staff.pk,
            "agreement_text": "Approved wording. " * 30,
            "terms_approved": True,
        },
        format="json",
    )
    assert bad.status_code == 400


def test_public_challenge_discloses_nothing_and_attempts_persist(setup):
    doc = prepare(setup)
    token, url = invitation(setup[2], doc)
    public = APIClient()
    assert public.get(url + "document/").status_code == 403
    good = public.post(url + "request-code/")
    unknown = public.post("/api/v1/signing/" + "x" * 43 + "/request-code/")
    assert good.json() == unknown.json()
    assert len(mail.outbox) == 1
    code = re.search(r"code is (\d{6})", mail.outbox[-1].body)[1]
    public.post(url + "request-code/")
    assert len(mail.outbox) == 1
    wrong = "999999" if code != "999999" else "111111"
    for _ in range(5):
        assert public.post(url + "verify/", {"code": wrong}).status_code == 400
    invite = SigningInvite.objects.get(token_hash=digest(token.encode()))
    assert invite.otp_attempts == 5 and code not in invite.otp_hash
    assert public.post(url + "verify/", {"code": code}).status_code == 400
    assert public.get(url + "pdf/").status_code == 403


@pytest.mark.parametrize("change", ["expiry", "session", "revoke", "supersede", "suspend"])
def test_grant_revocation_rechecked_on_read(setup, change):
    org, _, client, _ = setup
    doc = prepare(setup)
    public, token, url = verified(client, doc)
    assert public.get(url + "document/").status_code == 200
    invite = SigningInvite.objects.get(token_hash=digest(token.encode()))
    if change == "expiry":
        invite.expires_at = timezone.now() - timedelta(seconds=1)
        invite.save()
    elif change == "session":
        invite.session_expires_at = timezone.now() - timedelta(seconds=1)
        invite.save()
    elif change == "revoke":
        assert client.post(f"{ROOT}{doc['id']}/revoke/").status_code == 200
    elif change == "supersede":
        prepare(setup)
    else:
        org.is_active = False
        org.save()
    assert public.get(url + "document/").status_code == 403
    assert public.get(url + "pdf/").status_code == 403


@pytest.mark.parametrize("change", ["terms", "membership", "tenant", "ended", "signer_email"])
def test_changed_terms_or_authority_reject_signing(setup, change):
    org, user, client, lease = setup
    doc = prepare(setup)
    if change == "terms":
        lease.monthly_rent = "2000.00"
        lease.save()
    elif change == "membership":
        OrganizationMembership.objects.filter(user=user).update(is_active=False)
    elif change == "tenant":
        lease.tenant.is_active = False
        lease.tenant.save()
    elif change == "ended":
        lease.status = "ended"
        lease.save()
    else:
        user.email = "changed@example.com"
        user.save()
    assert client.post(f"{ROOT}{doc['id']}/sign/", sign_payload(doc)).status_code in {400, 403}
    assert not DocumentVersion.objects.get().signatures.exists()


def test_upload_pdf_source_and_exact_original_preservation(setup):
    doc = prepare(setup)
    raw = bytes(DocumentVersion.objects.get().pdf)
    client = setup[2]
    preview = client.post(ROOT + "source-preview/", {"file": SimpleUploadedFile("scan.pdf", raw)})
    assert preview.status_code == 200, preview.content
    assert preview.json()["response_data"]["pages"] == doc["page_count"]
    attach = client.post(
        "/api/v1/documents/originals/",
        {
            "lease": str(setup[3].public_id),
            "file": SimpleUploadedFile("signed.pdf", raw),
            "note": "Original supplied by tenant",
            "confirmed_original": True,
        },
    )
    assert attach.status_code == 201, attach.content
    assert bytes(SignedLeaseOriginal.objects.get().pdf) == raw
    bad = client.post(
        ROOT + "source-preview/",
        {
            "file": SimpleUploadedFile("bad.pdf", b"%PDF-fake"),
        },
    )
    assert bad.status_code == 400
    oversized = client.post(
        ROOT + "source-preview/",
        {
            "file": SimpleUploadedFile("large.png", b"a" * (4 * 1024**2 + 1)),
        },
    )
    assert oversized.status_code == 400


def test_render_failure_rolls_back_and_invite_delivery_failure_is_actionable(setup):
    doc = prepare(setup)
    client = setup[2]
    with patch("apps.documents.signing.lease_pdf", side_effect=ValueError("Broken renderer")):
        with pytest.raises(ValueError):
            client.post(f"{ROOT}{doc['id']}/sign/", sign_payload(doc))
    assert not DocumentVersion.objects.get().signatures.exists()
    with patch("apps.documents.signing.send_mail", side_effect=OSError("Provider failure")):
        response = client.post(f"{ROOT}{doc['id']}/invite/", {"email_link": True})
    assert response.status_code == 400
    assert not SigningInvite.objects.exists()


def test_request_code_throttling(setup):
    doc = prepare(setup)
    _, url = invitation(setup[2], doc)
    public = APIClient()
    for _ in range(5):
        assert public.post(url + "request-code/").status_code == 200
    assert public.post(url + "request-code/").status_code == 429


def test_delivery_failure_retains_completed_document_and_retry_is_idempotent(
    setup, django_capture_on_commit_callbacks
):
    from .signing import send_completed_copies

    doc = prepare(setup)
    client = setup[2]
    public, _, url = verified(client, doc)
    first = client.post(f"{ROOT}{doc['id']}/sign/", sign_payload(doc)).json()["response_data"]
    with patch("apps.documents.signing.EmailMessage.send", side_effect=OSError("Unavailable")):
        with django_capture_on_commit_callbacks(execute=True):
            result = public.post(url + "sign/", sign_payload(first, setup[3].tenant.full_name))
    assert result.status_code == 200
    record = DocumentVersion.objects.get()
    assert record.status == "signed" and record.delivery_failed
    assert not record.copies_emailed_at and record.signatures.count() == 2
    before = len(mail.outbox)
    assert send_completed_copies(record.pk)
    assert send_completed_copies(record.pk)
    assert len(mail.outbox) == before + 1
    record.refresh_from_db()
    assert record.copies_emailed_at and not record.delivery_failed


def test_console_email_backend_never_logs_verification_secrets(setup, settings, capsys):
    doc = prepare(setup)
    token, url = invitation(setup[2], doc)
    settings.EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    assert APIClient().post(url + "request-code/").status_code == 200
    invite = SigningInvite.objects.get(token_hash=digest(token.encode()))
    assert not invite.otp_hash
    output = capsys.readouterr()
    assert "verification code is" not in output.out and "Subject:" not in output.out
    response = setup[2].post(f"{ROOT}{doc['id']}/invite/", {"email_link": True})
    assert response.status_code == 400
    invite.refresh_from_db()
    assert not invite.revoked_at  # Failed delivery leaves the previous invitation valid.


def test_otp_expiry_replay_and_verification_session_is_bound_to_link(setup):
    doc = prepare(setup)
    token, url = invitation(setup[2], doc)
    public = APIClient()
    public.post(url + "request-code/")
    code = re.search(r"code is (\d{6})", mail.outbox[-1].body)[1]
    invite = SigningInvite.objects.get(token_hash=digest(token.encode()))
    invite.otp_expires_at = timezone.now() - timedelta(seconds=1)
    invite.save()
    assert public.post(url + "verify/", {"code": code}).status_code == 400
    invite.otp_expires_at = timezone.now() + timedelta(minutes=1)
    invite.save()
    result = public.post(url + "verify/", {"code": code})
    assert result.status_code == 200
    assert public.post(url + "verify/", {"code": code}).status_code == 400
    public.credentials(HTTP_X_DWELLA_SIGNING_SESSION=result.json()["response_data"]["session"])
    _, other_url = invitation(setup[2], doc)
    assert public.get(other_url + "document/").status_code == 403
    assert public.get(url + "document/").status_code == 403


def test_originals_are_private_and_do_not_accept_foreign_leases(setup):
    doc = prepare(setup)
    raw = bytes(DocumentVersion.objects.get().pdf)
    _, other = member(Organization.objects.create(name="Other records"), "outsider")
    payload = {
        "lease": str(setup[3].public_id),
        "file": SimpleUploadedFile("original.pdf", raw),
        "note": "Tenant supplied original",
        "confirmed_original": True,
    }
    assert other.post("/api/v1/documents/originals/", payload).status_code == 400
    payload["file"] = SimpleUploadedFile("original.pdf", raw)
    result = setup[2].post("/api/v1/documents/originals/", payload)
    original_id = result.json()["response_data"]["id"]
    path = f"/api/v1/documents/originals/{original_id}/pdf/"
    assert other.get(path).status_code == 404
    assert APIClient().get(path).status_code == 403
    assert not doc.get("pdf")
    assert setup[2].get(f"{ROOT}{doc['id']}/signatures/not-a-uuid/pdf/").status_code == 404


def test_support_can_manage_documents_but_cannot_sign_for_landlord(setup):
    from apps.audit.models import AuditEvent
    from apps.audit.support_test_utils import start

    org, _, _, _ = setup
    doc = prepare(setup)
    staff, client = member(org, "administrator")
    staff.is_staff = True
    staff.save()
    assert client.get(ROOT).status_code == 400
    start(client, org)
    assert client.get(ROOT).status_code == 200
    assert client.post(f"{ROOT}{doc['id']}/sign/", sign_payload(doc)).status_code == 403
    assert client.post(f"{ROOT}{doc['id']}/invite/", {}).status_code == 200
    assert AuditEvent.objects.filter(action="document.signing_invited", actor=staff).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_signatures_cannot_both_apply_to_the_same_digest(setup):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connection

    if connection.vendor != "postgresql":
        pytest.skip("Requires real row locks")
    doc = prepare(setup)
    user = setup[1]
    gate = Barrier(2)

    def sign_once():
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user=user)
            gate.wait(timeout=10)
            return client.post(f"{ROOT}{doc['id']}/sign/", sign_payload(doc)).status_code
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(sign_once) for _ in range(2)]
        assert sorted(f.result(timeout=20) for f in futures) == [200, 400]
    assert DocumentVersion.objects.get().signatures.count() == 1


def test_large_invoice_payment_history_flows_across_pdf_pages(setup):
    from .rendering import invoice_pdf
    from .snapshots import invoice_source

    org, _, _, lease = setup
    lease.status = "active"
    lease.save()
    generate_rent_invoices(org, timezone.localdate().replace(day=1))
    snapshot = invoice_source(Invoice.objects.get())
    snapshot["version"] = 1
    snapshot["payments"] = [
        {
            "receipt": f"RCT-{index:04}",
            "date": "2026-10-24",
            "method": "Bank transfer",
            "amount": "20.00",
        }
        for index in range(45)
    ]
    raw, pages = invoice_pdf(snapshot)
    assert pages >= 3
    assert inspect_pdf(raw, render=False)["pages"] == pages


def test_signature_normalization_removes_source_metadata_and_white_margins():
    from PIL.PngImagePlugin import PngInfo

    from .files import clean_image

    source = Image.new("RGB", (500, 300), "white")
    ImageDraw.Draw(source).line([(100, 200), (200, 100), (350, 210)], fill="black", width=4)
    source.info["icc_profile"] = b"source-profile"
    metadata = PngInfo()
    metadata.add_text("Comment", "private source metadata")
    raw = io.BytesIO()
    source.save(raw, "PNG", pnginfo=metadata)
    normalized = clean_image(raw.getvalue(), signature=True)
    with Image.open(io.BytesIO(normalized)) as result:
        assert not result.info
        assert result.width < 300 and result.height < 150
