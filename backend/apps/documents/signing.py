import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.services import record_event
from apps.common.mail import delivery_configured
from apps.leases.models import Lease
from apps.subscriptions.catalog import Feature
from apps.subscriptions.services import require_feature

from .files import MAX_SIGNATURE_BYTES, clean_image, read_upload
from .models import DocumentSignature, DocumentVersion, SigningEmail, SigningInvite
from .outbox import cipher, enqueue
from .rendering import digest, lease_pdf
from .services import active_signer, require_current, validate_pdf_size

logger = logging.getLogger(__name__)
INVALID = "This signing link or verification has expired or is unavailable."
CONSENT = (
    "I confirm my identity, have reviewed this complete agreement and its schedules, "
    "and intend this signature to apply to this document version."
)


def invite_for_token(token, *, lock=False, read=False):
    if not 20 <= len(token) <= 100:
        return None
    query = SigningInvite.objects.select_related(
        "document__organization", "document__lease", "document__landlord_signer"
    )
    if lock:
        query = query.select_for_update(of=("self",))
    invite = query.filter(token_hash=digest(token.encode())).first()
    if (
        not invite
        or invite.revoked_at
        or invite.expires_at <= timezone.now()
        or not invite.document.organization.is_active
        or invite.document.status in {"revoked", "superseded"}
        or (invite.consumed_at and not read)
    ):
        return None
    if not read or invite.document.status != "signed":
        try:
            require_current(invite.document)
        except ValidationError:
            return None
    return invite


def require_email_delivery():
    if not delivery_configured():
        raise ValidationError("Email delivery is not configured. Contact Dwella support.")


def verified_invite(request, token, *, read=False):
    invite = invite_for_token(token, read=read)
    session = request.headers.get("X-Dwella-Signing-Session", "")
    if (
        not invite
        or not 20 <= len(session) <= 100
        or not invite.session_hash
        or not secrets.compare_digest(invite.session_hash, digest(session.encode()))
        or not invite.session_expires_at
        or invite.session_expires_at <= timezone.now()
    ):
        raise PermissionDenied(INVALID)
    return invite


@transaction.atomic
def issue_invite(request, document, email_link=False):
    if email_link:
        require_email_delivery()
    # All signing writes take locks in the same order: document, then invitation.
    document = DocumentVersion.objects.select_for_update().get(pk=document.pk)
    require_current(document)
    require_feature(document.organization, Feature.LEASE_SIGNING)
    if document.signatures.filter(role="tenant").exists():
        raise ValidationError("The tenant has already signed this version.")
    document.invites.filter(revoked_at__isnull=True).update(
        revoked_at=timezone.now(),
        session_hash="",
    )
    token = secrets.token_urlsafe(32)
    invite = SigningInvite.objects.create(
        document=document,
        email=document.snapshot["tenant_email"],
        token_hash=digest(token.encode()),
        expires_at=timezone.now() + timedelta(days=7),
    )
    link = f"{settings.FRONTEND_URL.rstrip('/')}/sign/{token}"
    if email_link:
        # Explicit manager action only. Never accept a replacement recipient from the client.
        enqueue(document, SigningEmail.Kind.INVITATION, invite=invite,
                payload={"token": token}, expires_at=invite.expires_at,
                dedupe_key=f"invitation:{invite.pk}")
    document.status = "signing"
    document.save(update_fields=["status", "updated_at"])
    record_event(
        request, "document.signing_invited", document, document.organization, emailed=email_link
    )
    return {"url": link, "expires_at": invite.expires_at, "email_queued": email_link}


def request_code(request, token):
    # Do not disclose validity, tenant names, email addresses or document details.
    invite = invite_for_token(token)
    if not invite:
        return
    now = timezone.now()
    with transaction.atomic():
        document = DocumentVersion.objects.select_for_update().get(pk=invite.document_id)
        invite = invite_for_token(token, lock=True)
        if not invite or (
            invite.otp_requested_at and invite.otp_requested_at > now - timedelta(seconds=60)
        ):
            return
        require_current(document)
        code = f"{secrets.randbelow(1_000_000):06d}"
        invite.otp_hash = make_password(code)
        invite.otp_expires_at = now + timedelta(minutes=10)
        invite.otp_requested_at = now
        invite.otp_attempts = 0
        invite.save()
        try:
            require_email_delivery()
            enqueue(document, SigningEmail.Kind.OTP, invite=invite, payload={"code": code},
                    expires_at=invite.otp_expires_at,
                    dedupe_key=f"otp:{invite.pk}:{digest(invite.otp_hash.encode())}")
        except Exception:
            # Same public response if delivery fails. No code or recipient in application logs.
            invite.otp_hash = ""
            invite.save(update_fields=["otp_hash"])
            logger.warning("Signing verification delivery failed")
        record_event(request, "document.signing_challenge", document, document.organization)


def verify_code(request, token, code):
    session = None
    invite = invite_for_token(token)
    if invite:
        with transaction.atomic():
            DocumentVersion.objects.select_for_update().get(pk=invite.document_id)
            invite = invite_for_token(token, lock=True)
            if (
                invite
                and invite.otp_hash
                and invite.otp_expires_at
                and invite.otp_expires_at > timezone.now()
                and invite.otp_attempts < 5
            ):
                invite.otp_attempts += 1
                if check_password(code, invite.otp_hash):
                    session = secrets.token_urlsafe(32)
                    invite.session_hash = digest(session.encode())
                    invite.session_expires_at = min(
                        invite.expires_at,
                        timezone.now() + timedelta(minutes=20),
                    )
                    invite.otp_hash = ""
                invite.save()
    # Raise outside atomic so failed-attempt counters are not rolled back.
    if not session:
        raise ValidationError(INVALID)
    record_event(
        request,
        "document.signer_verified",
        invite.document,
        invite.document.organization,
        authentication="email_otp",
    )
    return {"session": session, "expires_at": invite.session_expires_at}


@transaction.atomic
def send_completed_copies(document_id):
    """Queue a durable intent; delivery runs only in the separate outbox worker."""
    document = DocumentVersion.objects.select_for_update().get(pk=document_id)
    if document.copies_emailed_at or document.status != "signed":
        return not document.delivery_failed
    row = enqueue(document, SigningEmail.Kind.COMPLETED,
                  dedupe_key=f"completed:{document.pk}:{document.sha256}")
    if row.status in {SigningEmail.Status.FAILED, SigningEmail.Status.CANCELLED}:
        SigningEmail.objects.filter(pk=row.pk).update(
            status=SigningEmail.Status.PENDING, attempts=0, next_attempt_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=7), failure_code="",
            encrypted_payload=cipher().encrypt(b"{}"),
        )
        DocumentVersion.objects.filter(pk=document.pk).update(delivery_failed=False)
    return bool(document.copies_emailed_at)


def add_signature(request, document, data, *, invite=None):
    if document.kind != "lease":
        raise ValidationError("Only a lease agreement can be signed.")
    role = "tenant" if invite else "landlord"
    raw = clean_image(read_upload(data["signature"], MAX_SIGNATURE_BYTES), signature=True)
    with transaction.atomic():
        Lease.objects.select_for_update().get(pk=document.lease_id)
        document = DocumentVersion.objects.select_for_update().get(pk=document.pk)
        require_current(document)
        if document.sha256 != data["expected_sha256"]:
            raise ValidationError("The document changed. Review its latest PDF before signing.")
        if document.signatures.filter(role=role).exists():
            raise ValidationError("This party has already signed this document version.")
        if invite:
            invite = verified_invite(request, data["token"])
            invite = SigningInvite.objects.select_for_update().get(pk=invite.pk)
            if invite.document_id != document.pk:
                raise PermissionDenied(INVALID)
            name, email, user = document.snapshot["tenant_name"], invite.email, None
        else:
            user = request.user
            if user.pk != document.landlord_signer_id or not active_signer(
                user, document.organization
            ):
                raise PermissionDenied(
                    "Only the designated property manager can sign for the landlord."
                )
            name, email = (
                document.snapshot["landlord_signer_name"],
                document.snapshot["landlord_signer_email"],
            )
        if data["signer_name"].strip().casefold() != name.strip().casefold():
            raise ValidationError({"signer_name": ["Enter the name shown on this agreement."]})
        signature = DocumentSignature.objects.create(
            document=document,
            role=role,
            signer_name=name,
            signer_email=email,
            user=user,
            authentication_method="email_otp" if invite else "account",
            source=data["source"],
            png=raw,
            consent=CONSENT,
            signed_at=timezone.now(),
            reviewed_sha256=document.sha256,
            signed_pdf=b"",
            sha256="",
        )
        signatures = list(document.signatures.order_by("signed_at"))
        signed_pdf, pages = lease_pdf(document.snapshot, signatures)
        validate_pdf_size(signed_pdf, pages)
        signature.signed_pdf = signed_pdf
        signature.sha256 = digest(signed_pdf)
        signature.save(update_fields=["signed_pdf", "sha256"])
        document.pdf, document.sha256, document.page_count = signed_pdf, signature.sha256, pages
        document.status = "signed" if len(signatures) == 2 else "signing"
        document.save(update_fields=["pdf", "sha256", "page_count", "status", "updated_at"])
        if invite:
            invite.consumed_at = timezone.now()
            invite.otp_hash = ""
            invite.save(update_fields=["consumed_at", "otp_hash"])
        record_event(
            request,
            "document.signed",
            document,
            document.organization,
            role=role,
            authentication=signature.authentication_method,
            reviewed_sha256=signature.reviewed_sha256,
            sha256=document.sha256,
        )
        if document.status == "signed":
            send_completed_copies(document.pk)
    return document


@transaction.atomic
def revoke_signing(request, document):
    document = DocumentVersion.objects.select_for_update().get(pk=document.pk)
    if document.kind != "lease" or document.status == "signed":
        raise ValidationError("Completed documents are preserved and cannot be revoked.")
    document.invites.filter(revoked_at__isnull=True).update(
        revoked_at=timezone.now(),
        session_hash="",
        otp_hash="",
    )
    document.status = "revoked"
    document.save(update_fields=["status", "updated_at"])
    record_event(request, "document.signing_revoked", document, document.organization)
    return document
