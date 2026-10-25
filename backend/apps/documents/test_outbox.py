import json
import threading
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.db import close_old_connections, connection, transaction
from django.utils import timezone

from apps.billing.tests import make_lease
from apps.organizations.models import Organization, OrganizationMembership

from .models import DocumentVersion, SigningEmail, SigningInvite
from .outbox import cipher, deliver_pending
from .rendering import digest
from .tests import invitation, member, prepare

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def mail_settings(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.OUTBOUND_EMAIL_ALLOWLIST = []
    mail.outbox = []
    cache.clear()


@pytest.fixture
def setup():
    org = Organization.objects.create(name="Outbox test workspace")
    user, client = member(org)
    lease = make_lease(org, active=False)
    lease.tenant.email = "tenant@example.com"
    lease.tenant.save()
    return org, user, client, lease


def queued_code(setup):
    doc = prepare(setup)
    token, url = invitation(setup[2], doc)
    from rest_framework.test import APIClient
    assert APIClient().post(url + "request-code/").status_code == 200
    return doc, token, SigningEmail.objects.get(kind="otp")


def test_requests_commit_encrypted_intents_without_smtp(setup):
    with patch.object(EmailMessage, "send", side_effect=AssertionError("SMTP in request")):
        doc, token, row = queued_code(setup)
    invite = SigningInvite.objects.get(token_hash=digest(token.encode()))
    payload = json.loads(cipher().decrypt(bytes(row.encrypted_payload)))
    assert payload["code"].encode() not in bytes(row.encrypted_payload)
    assert len(payload["code"]) == 6 and invite.otp_hash
    assert not mail.outbox
    original_send = EmailMessage.send

    def send(message, **kwargs):
        assert not connection.in_atomic_block
        return original_send(message, **kwargs)

    with patch.object(EmailMessage, "send", autospec=True, side_effect=send):
        assert deliver_pending() == 1
    row.refresh_from_db()
    assert row.status == "sent" and not row.encrypted_payload and row.sent_at
    assert deliver_pending() == 0 and len(mail.outbox) == 1
    assert "Message-ID" in mail.outbox[0].extra_headers


def test_invite_transaction_rollback_leaves_nothing_to_send(setup):
    doc = prepare(setup)
    from .signing import issue_invite
    request = type("Request", (), {"user": setup[1], "META": {}})()
    with pytest.raises(RuntimeError, match="rollback"), transaction.atomic():
        issue_invite(request, DocumentVersion.objects.get(public_id=doc["id"]), email_link=True)
        raise RuntimeError("rollback")
    assert not SigningInvite.objects.exists() and not SigningEmail.objects.exists()
    assert deliver_pending() == 0


@pytest.mark.parametrize("change", ["revoke", "supersede", "expiry", "consumed", "otp_expiry",
                                    "replaced_code", "membership", "suspended", "tenant_email"])
def test_stale_or_unauthorized_challenges_are_cancelled(setup, change):
    _, _, row = queued_code(setup)
    invite, document = row.invite, row.document
    if change == "revoke":
        invite.revoked_at = timezone.now()
    elif change == "consumed":
        invite.consumed_at = timezone.now()
    elif change == "expiry":
        invite.expires_at = timezone.now() - timedelta(seconds=1)
    elif change == "otp_expiry":
        invite.otp_expires_at = timezone.now() - timedelta(seconds=1)
    elif change == "replaced_code":
        invite.otp_hash = "invalid"
    elif change == "supersede":
        document.status = "superseded"
        document.save()
    elif change == "membership":
        OrganizationMembership.objects.filter(user=setup[1]).update(is_active=False)
    elif change == "suspended":
        setup[0].is_active = False
        setup[0].save()
    else:
        setup[3].tenant.email = "different@example.com"
        setup[3].tenant.save()
    invite.save()
    assert deliver_pending() == 0
    row.refresh_from_db()
    assert row.status == "cancelled" and not row.encrypted_payload
    assert not mail.outbox


def test_failed_delivery_is_bounded_and_does_not_log_secrets(setup, caplog):
    _, _, row = queued_code(setup)
    with patch.object(EmailMessage, "send", side_effect=OSError("secret-provider-context")):
        assert deliver_pending() == 0
        row.refresh_from_db()
        assert row.status == "pending" and row.attempts == 1 and row.encrypted_payload
        assert row.next_attempt_at > timezone.now()
        assert deliver_pending() == 0
        for _ in range(4):
            SigningEmail.objects.filter(pk=row.pk).update(next_attempt_at=timezone.now())
            assert deliver_pending() == 0
    row.refresh_from_db()
    assert row.status == "failed" and row.attempts == 5 and not row.encrypted_payload
    assert "secret-provider-context" not in caplog.text


def test_recipient_guard_blocks_before_smtp(setup, settings):
    _, _, row = queued_code(setup)
    settings.OUTBOUND_EMAIL_ALLOWLIST = ["allowed@example.com"]
    with patch.object(EmailMessage, "send") as send:
        assert deliver_pending() == 0
    send.assert_not_called()
    row.refresh_from_db()
    assert row.status == "failed" and row.failure_code == "recipient_restricted"


def test_outbox_does_not_run_in_a_caller_transaction():
    with transaction.atomic(), pytest.raises(RuntimeError, match="outside"):
        deliver_pending()


def test_key_rotation_can_decrypt_pending_payloads(settings):
    encrypted = cipher().encrypt(b'{"code":"123456"}')
    previous = settings.SECRET_KEY
    settings.SECRET_KEY = "a-new-key-that-is-used-only-in-this-test"
    settings.SECRET_KEY_FALLBACKS = [previous]
    assert cipher().decrypt(encrypted) == b'{"code":"123456"}'


def test_slow_smtp_holds_no_document_lock_and_other_workers_do_not_duplicate(setup):
    if connection.vendor != "postgresql":
        pytest.skip("Real competing PostgreSQL connections required")
    _, _, row = queued_code(setup)
    entered, release = threading.Event(), threading.Event()
    errors = []

    def slow_send(message, **kwargs):
        assert not connection.in_atomic_block
        entered.set()
        assert release.wait(10)
        return 1

    def worker():
        close_old_connections()
        try:
            deliver_pending()
        except Exception as error:
            errors.append(type(error).__name__)
        finally:
            close_old_connections()

    with patch.object(EmailMessage, "send", autospec=True, side_effect=slow_send):
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            assert entered.wait(10)
            with transaction.atomic():
                DocumentVersion.objects.select_for_update(nowait=True).get(pk=row.document_id)
            assert deliver_pending() == 0
        finally:
            release.set()
            thread.join(15)
    assert not thread.is_alive() and not errors
    row.refresh_from_db()
    assert row.status == "sent" and row.attempts == 1
