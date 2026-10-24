import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import EmailMessage, send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.services import record_event
from apps.leases.models import Lease

from .files import MAX_SIGNATURE_BYTES, clean_image, read_upload
from .models import DocumentSignature, DocumentVersion, SigningInvite
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
    if settings.EMAIL_BACKEND in {
        "django.core.mail.backends.console.EmailBackend",
        "django.core.mail.backends.dummy.EmailBackend",
    }:
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
    # All signing writes take locks in the same order: document, then invitation.
    document = DocumentVersion.objects.select_for_update().get(pk=document.pk)
    require_current(document)
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
        try:
            require_email_delivery()
            sent = send_mail(
                f"Review and sign lease {document.snapshot['reference']}",
                f"You have been invited to review a lease agreement.\n\n{link}\n\n"
                "The link expires in 7 days. "
                "We will verify your email before showing the agreement.",
                settings.DEFAULT_FROM_EMAIL,
                [invite.email],
                fail_silently=False,
            )
            if sent != 1:
                raise RuntimeError("Delivery unavailable")
        except Exception as error:
            raise ValidationError("Invitation could not be delivered. Please try again.") from error
    document.status = "signing"
    document.save(update_fields=["status", "updated_at"])
    record_event(
        request, "document.signing_invited", document, document.organization, emailed=email_link
    )
    return {"url": link, "expires_at": invite.expires_at}


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
            send_mail(
                "Your Dwella lease verification code",
                f"Your verification code is {code}. It expires in 10 minutes.\n\n"
                "This code only opens your lease for review; entering it does not sign anything.",
                settings.DEFAULT_FROM_EMAIL,
                [invite.email],
                fail_silently=False,
            )
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
    document = DocumentVersion.objects.select_for_update().get(pk=document_id)
    if document.copies_emailed_at or document.status != "signed":
        return not document.delivery_failed
    recipients = list(
        dict.fromkeys(
            filter(
                None,
                [document.snapshot["tenant_email"], document.snapshot["landlord_signer_email"]],
            )
        )
    )
    try:
        require_email_delivery()
        message = EmailMessage(
            f"Signed lease {document.snapshot['reference']} · v{document.version}",
            "All required signatures have been recorded. Your completed agreement and signing "
            "record are attached. This does not change the tenancy's activation status.",
            settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach(
            f"{document.snapshot['reference']}-v{document.version}.pdf",
            bytes(document.pdf),
            "application/pdf",
        )
        if not recipients or message.send(fail_silently=False) != 1:
            raise RuntimeError("Delivery unavailable")
    except Exception:
        DocumentVersion.objects.filter(pk=document.pk).update(delivery_failed=True)
        logger.warning("Signed-document copy delivery failed")
        return False
    DocumentVersion.objects.filter(pk=document.pk).update(
        copies_emailed_at=timezone.now(),
        delivery_failed=False,
    )
    return True


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
            transaction.on_commit(lambda: send_completed_copies(document.pk))
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
