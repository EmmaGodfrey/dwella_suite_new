from smtplib import SMTPException
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework.authtoken.models import Token

from apps.accounts.models import TwoFactorDevice

from .models import AuditEvent

pytestmark = pytest.mark.django_db


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_credential_actions_revoke_tokens_and_audit(context):
    client, _, _, _ = context
    user = get_user_model().objects.create_user(username="target", email="target@example.com")
    path = f"/api/v1/platform/users/{user.pk}/"
    Token.objects.create(user=user)
    TwoFactorDevice.objects.create(user=user, secret="test-device", is_confirmed=True)
    assert client.post(path + "password-reset/").status_code == 200
    assert len(mail.outbox) == 1
    assert client.post(path + "reset-2fa/").status_code == 200
    assert not TwoFactorDevice.objects.filter(user=user).exists()
    assert not Token.objects.filter(user=user).exists()
    Token.objects.create(user=user)
    assert client.post(path + "sign-out/").status_code == 200
    assert not Token.objects.filter(user=user).exists()
    assert AuditEvent.objects.filter(resource_id=str(user.pk)).count() == 3


def test_email_failure_is_explicit_and_does_not_report_a_success(context):
    client, _, _, _ = context
    user = get_user_model().objects.create_user(username="target", email="target@example.com")
    with patch("apps.audit.user_security_actions.send_access_email", side_effect=SMTPException):
        assert client.post(
            f"/api/v1/platform/users/{user.pk}/password-reset/"
        ).status_code == 503
    assert not AuditEvent.objects.filter(action="user.password_reset_sent").exists()


@pytest.mark.parametrize("action", ["password-reset", "reset-2fa", "sign-out"])
def test_non_staff_cannot_change_other_account_security(context, action):
    client, actor, _, _ = context
    user = get_user_model().objects.create_user(username="ordinary")
    client.force_authenticate(user)
    assert client.post(f"/api/v1/platform/users/{actor.pk}/{action}/").status_code == 403
