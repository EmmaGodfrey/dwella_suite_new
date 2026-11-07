import importlib

import pytest
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives, get_connection
from django.test import override_settings

from apps.accounts.account_mail import send_account_mail

from .mail import ALLOWLIST_BACKEND, recipient_allowed

REDIRECT = {
    "APP_ENVIRONMENT": "test",
    "TEST_EMAIL_REDIRECT_TO": "sink@example.com",
    "EMAIL_BACKEND": ALLOWLIST_BACKEND,
    "OUTBOUND_INNER_EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "OUTBOUND_EMAIL_ALLOWLIST": ["different@example.com"],
}


@override_settings(**REDIRECT)
def test_all_envelope_recipients_redirect_without_changing_message_content():
    message = EmailMultiAlternatives(
        "Invitation",
        "Private invitation link",
        "sender@example.com",
        ["new-tenant@example.com"],
        cc=["cc@example.com"],
        bcc=["hidden@example.com"],
        headers={"To": "override@example.com", "Cc": "override-cc@example.com"},
    )
    message.attach_alternative("<p>Invitation</p>", "text/html")
    assert message.send() == 1
    sent = mail.outbox[-1]
    assert sent.recipients() == ["sink@example.com"]
    assert sent.cc == [] and sent.bcc == []
    assert sent.subject == "[TEST] Invitation"
    assert sent.from_email == "sender@example.com"
    assert sent.body == "Private invitation link"
    assert sent.alternatives[0][0] == "<p>Invitation</p>"
    assert "new-tenant@example.com" in sent.extra_headers["X-Dwella-Original-Recipients"]
    assert "To" not in sent.extra_headers and "Cc" not in sent.extra_headers


@override_settings(**REDIRECT)
def test_invitation_and_outbox_prechecks_accept_new_addresses_only_for_redirection():
    assert recipient_allowed("new-tenant@example.com")
    assert not recipient_allowed("")
    assert not recipient_allowed("0770000000")
    assert send_account_mail("Account link", "Body", "new-tenant@example.com") is True
    assert mail.outbox[-1].to == ["sink@example.com"]


@pytest.mark.parametrize("environment", ["production", "staging", "development"])
def test_redirection_refuses_non_test_environments(environment):
    with override_settings(**{**REDIRECT, "APP_ENVIRONMENT": environment}):
        with pytest.raises(ImproperlyConfigured):
            get_connection()


@pytest.mark.parametrize(
    "recipient", ["invalid", "a@example.com,b@example.com", "a@example.com\r\nBcc:x@example.com"]
)
def test_invalid_redirect_targets_are_rejected(recipient):
    with override_settings(**{**REDIRECT, "TEST_EMAIL_REDIRECT_TO": recipient}):
        with pytest.raises(ImproperlyConfigured):
            get_connection()


def test_settings_wrap_smtp_even_without_an_allowlist(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "test")
    monkeypatch.setenv("TEST_EMAIL_REDIRECT_TO", "sink@example.com")
    monkeypatch.setenv("APP_OUTBOUND_EMAIL_ALLOWLIST", "")
    monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    monkeypatch.setenv("APP_EMAIL_ROUTING_ENABLED", "false")
    spec = importlib.util.find_spec("config.settings")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.EMAIL_BACKEND == ALLOWLIST_BACKEND
    assert module.OUTBOUND_INNER_EMAIL_BACKEND == "apps.common.runtime_mail.RuntimeEmailBackend"
    assert module.RUNTIME_MAIL_INNER_BACKEND == "django.core.mail.backends.smtp.EmailBackend"


def test_production_settings_reject_a_catch_all(monkeypatch):
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("TEST_EMAIL_REDIRECT_TO", "sink@example.com")
    spec = importlib.util.find_spec("config.settings")
    module = importlib.util.module_from_spec(spec)
    with pytest.raises(ImproperlyConfigured):
        spec.loader.exec_module(module)
