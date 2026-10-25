import importlib

from django.core import mail
from django.core.mail import EmailMessage, send_mail
from django.test import override_settings

from apps.accounts.account_mail import send_account_mail

from .mail import ALLOWLIST_BACKEND, delivery_configured, recipient_allowed

GUARDED = {
    "EMAIL_BACKEND": ALLOWLIST_BACKEND,
    "OUTBOUND_INNER_EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "OUTBOUND_EMAIL_ALLOWLIST": ["eglabs.dev@gmail.com", "@tester.example"],
}


def test_allowlist_matches_addresses_and_domains():
    allowlist = GUARDED["OUTBOUND_EMAIL_ALLOWLIST"]
    assert recipient_allowed("EGLabs.Dev@Gmail.com", allowlist)
    assert recipient_allowed("Tester <ann@tester.example>", allowlist)
    assert not recipient_allowed("tenant@example.com", allowlist)
    assert not recipient_allowed("eglabs.dev@gmail.com.evil.example", allowlist)
    assert not recipient_allowed("ann@nottester.example.com", allowlist)
    assert recipient_allowed("anyone@example.com", [])


@override_settings(**GUARDED)
def test_only_listed_recipients_receive_email():
    message = EmailMessage(
        "Hello",
        "Body",
        "no-reply@dwella.local",
        to=["tenant@example.com", "eglabs.dev@gmail.com"],
        cc=["ann@tester.example", "landlord@example.com"],
        bcc=["hidden@example.com"],
    )
    assert message.send() == 1
    assert mail.outbox[-1].to == ["eglabs.dev@gmail.com"]
    assert mail.outbox[-1].cc == ["ann@tester.example"]
    assert mail.outbox[-1].bcc == []


@override_settings(**GUARDED)
def test_message_without_listed_recipients_is_not_sent():
    assert send_mail("Hi", "Body", "no-reply@dwella.local", ["tenant@example.com"]) == 0
    assert mail.outbox == []
    # Callers that require delivery see it as not delivered.
    assert send_account_mail("Reset", "Body", "tenant@example.com") is False
    assert send_account_mail("Reset", "Body", "eglabs.dev@gmail.com") is True


@override_settings(
    **{**GUARDED, "OUTBOUND_INNER_EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend"}
)
def test_delivery_checks_look_through_the_guard():
    # A guarded console backend must not be mistaken for real delivery.
    assert not delivery_configured()
    assert send_account_mail("Reset", "secret link", "eglabs.dev@gmail.com") is False


def test_setting_wraps_the_configured_backend(monkeypatch):
    monkeypatch.setenv("APP_OUTBOUND_EMAIL_ALLOWLIST", "eglabs.dev@gmail.com, @tester.example")
    monkeypatch.setenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
    spec = importlib.util.find_spec("config.settings")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.EMAIL_BACKEND == ALLOWLIST_BACKEND
    assert module.OUTBOUND_INNER_EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
    assert module.OUTBOUND_EMAIL_ALLOWLIST == ["eglabs.dev@gmail.com", "@tester.example"]
