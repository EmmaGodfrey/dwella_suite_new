"""Claim briefly, then send after commit with no signing or database locks held."""

import base64
import json
import uuid
from datetime import timedelta

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMessage
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import ValidationError

from apps.common.mail import delivery_configured, recipient_allowed

from .models import DocumentVersion, SigningEmail
from .rendering import digest
from .services import require_current

MAX_ATTEMPTS = 5
LEASE = timedelta(minutes=5)


def cipher():
    keys = [settings.SECRET_KEY, *settings.SECRET_KEY_FALLBACKS]
    return MultiFernet([
        Fernet(base64.urlsafe_b64encode(salted_hmac(
            "dwella.signing.email.encryption.v1", "payload", secret=key, algorithm="sha256",
        ).digest())) for key in keys
    ])


def enqueue(document, kind, *, invite=None, payload=None, expires_at=None, dedupe_key):
    row, _ = SigningEmail.objects.get_or_create(
        dedupe_key=dedupe_key,
        defaults={"document": document, "invite": invite, "kind": kind,
                  "encrypted_payload": cipher().encrypt(json.dumps(payload or {}).encode()),
                  "expires_at": expires_at or timezone.now() + timedelta(days=7),
                  "next_attempt_at": timezone.now()},
    )
    return row


def claim_next():
    now = timezone.now()
    due = Q(status="pending", next_attempt_at__lte=now) | Q(status="sending", locked_until__lte=now)
    with transaction.atomic():
        query = SigningEmail.objects.filter(due).order_by("created_at")
        query = query.select_for_update(
            skip_locked=connection.features.has_select_for_update_skip_locked,
        )
        row = query.first()
        if not row:
            return None
        old_status, old_attempts = row.status, row.attempts
        row.status, row.claim_token = SigningEmail.Status.SENDING, uuid.uuid4()
        row.attempts += 1
        row.locked_until = now + LEASE
        changed = SigningEmail.objects.filter(
            pk=row.pk, status=old_status, attempts=old_attempts,
        ).update(status=row.status, claim_token=row.claim_token,
                 attempts=row.attempts, locked_until=row.locked_until)
        return row if changed else None


def finish(row, status, *, failure="", retry=False):
    now = timezone.now()
    fields = {"status": status, "claim_token": None, "locked_until": None,
              "failure_code": failure}
    if retry:
        fields["next_attempt_at"] = now + timedelta(seconds=min(60 * 2 ** (row.attempts - 1), 900))
    else:
        fields["encrypted_payload"] = b""
    if status == SigningEmail.Status.SENT:
        fields["sent_at"] = now
    with transaction.atomic():
        changed = SigningEmail.objects.filter(
            pk=row.pk, status=SigningEmail.Status.SENDING, claim_token=row.claim_token,
        ).update(**fields)
        if changed and row.kind == SigningEmail.Kind.COMPLETED:
            if status == SigningEmail.Status.SENT:
                DocumentVersion.objects.filter(pk=row.document_id).update(
                    copies_emailed_at=now, delivery_failed=False,
                )
            elif failure or status == SigningEmail.Status.CANCELLED:
                DocumentVersion.objects.filter(
                    pk=row.document_id, copies_emailed_at__isnull=True,
                ).update(delivery_failed=True)


def message_for(row):
    document = row.document
    if row.expires_at <= timezone.now() or not document.organization.is_active:
        return None
    payload = json.loads(cipher().decrypt(bytes(row.encrypted_payload)))
    if row.kind == SigningEmail.Kind.COMPLETED:
        if document.status != "signed" or document.copies_emailed_at:
            return None
        recipients = list(dict.fromkeys(filter(None, [document.snapshot["tenant_email"],
                                           document.snapshot["landlord_signer_email"]])))
        message = EmailMessage(
            f"Signed lease {document.snapshot['reference']} · v{document.version}",
            "All required signatures have been recorded. Your completed agreement and signing "
            "record are attached. This does not change the tenancy's activation status.",
            settings.DEFAULT_FROM_EMAIL, to=recipients,
        )
        message.attach(f"{document.snapshot['reference']}-v{document.version}.pdf",
                       bytes(document.pdf), "application/pdf")
    else:
        invite = row.invite
        if (not invite or invite.document_id != document.pk or invite.revoked_at
                or invite.consumed_at or invite.expires_at <= timezone.now()
                or document.status in {"signed", "superseded", "revoked"}):
            return None
        try:
            require_current(document)
        except ValidationError:
            return None
        if row.kind == SigningEmail.Kind.OTP:
            if (not invite.otp_expires_at or invite.otp_expires_at <= timezone.now()
                    or not invite.otp_hash or not check_password(payload["code"], invite.otp_hash)):
                return None
            subject = "Your Dwella lease verification code"
            body = (f"Your verification code is {payload['code']}. It expires in 10 minutes.\n\n"
                    "This code only opens your lease for review; "
                    "entering it does not sign anything."
                    )
        else:
            if digest(payload["token"].encode()) != invite.token_hash:
                return None
            subject = f"Review and sign lease {document.snapshot['reference']}"
            link = f"{settings.FRONTEND_URL.rstrip('/')}/sign/{payload['token']}"
            body = (f"You have been invited to review a lease agreement.\n\n{link}\n\n"
                    "The link expires in 7 days. "
                    "We will verify your email before showing the agreement.")
        message = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, to=[invite.email])
    message.extra_headers["Message-ID"] = f"<dwella-signing-{row.public_id}@mail.dwella.properties>"
    return message


def deliver_pending(*, limit=20):
    if connection.in_atomic_block:
        raise RuntimeError("Outbox delivery must run outside a database transaction.")
    delivered = 0
    for _ in range(limit):
        row = claim_next()
        if not row:
            break
        row = SigningEmail.objects.select_related(
            "document__organization", "document__lease__tenant",
            "document__landlord_signer", "invite",
        ).get(pk=row.pk)
        if row.attempts > MAX_ATTEMPTS:
            finish(row, SigningEmail.Status.FAILED, failure="attempt_limit")
            continue
        try:
            message = message_for(row)
            if message is None:
                finish(row, SigningEmail.Status.CANCELLED)
                continue
            allowed = message.recipients() and all(
                recipient_allowed(a) for a in message.recipients()
            )
            if not allowed:
                finish(row, SigningEmail.Status.FAILED, failure="recipient_restricted")
                continue
            if not delivery_configured():
                raise RuntimeError("delivery_unavailable")
            if message.send(fail_silently=False) != 1:
                raise RuntimeError("delivery_unavailable")
        except Exception:
            retry = row.attempts < MAX_ATTEMPTS and row.expires_at > timezone.now()
            finish(row, SigningEmail.Status.PENDING if retry else SigningEmail.Status.FAILED,
                   failure="delivery_unavailable", retry=retry)
            continue
        finish(row, SigningEmail.Status.SENT)
        delivered += 1
    return delivered
