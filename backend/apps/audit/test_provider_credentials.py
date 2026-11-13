import json
import time
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from rest_framework.test import APIClient

from apps.accounts.models import TwoFactorDevice
from apps.accounts.security import _hotp, make_totp_secret
from apps.organizations.models import Organization, OrganizationMembership

from .models import AuditEvent, ProviderCredential, ProviderCredentialProof
from .provider_credentials import CredentialStoreUnavailable, credential, provider_credentials

pytestmark = pytest.mark.django_db
URL = "/api/v1/platform/provider-credentials/"
PASSWORD = "CredentialTestPassword42!"
SECRET = "synthetic-new-sms-api-key-123456789"


@pytest.fixture
def admin(settings):
    cache.clear()
    settings.APP_ENVIRONMENT = "test"
    settings.REQUIRE_ADMIN_MFA = False
    settings.PROVIDER_CREDENTIALS_ENABLED = True
    settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY_FALLBACKS = []
    settings.AFRICASTALKING_API_KEY = "synthetic-environment-key-123456789"
    user = get_user_model().objects.create_user(
        username="provider-admin", password=PASSWORD, is_staff=True, is_superuser=True
    )
    device = TwoFactorDevice.objects.create(user=user, secret=make_totp_secret(), is_confirmed=True)
    client = APIClient()
    client.force_authenticate(user)
    return client, user, device


def body(device, **extra):
    return {
        "password": PASSWORD,
        "code": _hotp(device.secret, int(time.time() // 30)),
        "values": {"AFRICASTALKING_API_KEY": SECRET},
        **extra,
    }


@pytest.mark.parametrize("role", [None, "tenant", "manager", "landlord", "staff"])
def test_only_superusers_can_read_or_replace_credentials(admin, role):
    _, _, device = admin
    client = APIClient()
    if role:
        user = get_user_model().objects.create_user(username=role, is_staff=role == "staff")
        if role != "staff":
            org = Organization.objects.create(name="Other workspace")
            OrganizationMembership.objects.create(user=user, organization=org, role=role)
        client.force_authenticate(user)
    for method, data in [("get", None), ("post", body(device))]:
        response = getattr(client, method)(URL, data, format="json")
        assert response.status_code in (401, 403)
    assert not ProviderCredential.objects.exists()


def test_replacement_is_encrypted_replace_only_audited_and_worker_visible(admin):
    client, user, device = admin
    assert credential("AFRICASTALKING_API_KEY").startswith("synthetic-environment")
    response = client.post(URL, body(device), format="json")
    assert response.status_code == 200, response.content
    row = ProviderCredential.objects.get()
    assert SECRET.encode() not in bytes(row.encrypted_value)
    assert row.updated_by == user
    for reply in (response, client.get(URL)):
        assert SECRET.encode() not in reply.content
        assert bytes(row.encrypted_value) not in reply.content
        assert reply["Cache-Control"] == "private, no-store"
    assert credential("AFRICASTALKING_API_KEY") == SECRET
    assert provider_credentials("RESEND_API_KEY")["RESEND_API_KEY"] is not None
    event = AuditEvent.objects.get(action="platform.provider_credentials_replaced")
    assert event.metadata == {"fields": ["AFRICASTALKING_API_KEY"]}
    assert SECRET not in json.dumps(event.metadata)
    assert PASSWORD not in json.dumps(event.metadata)


@pytest.mark.parametrize(
    "failure",
    ["password", "code", "missing_device", "unconfirmed", "disabled_user", "revoked_admin"],
)
def test_password_and_confirmed_fresh_authenticator_are_always_required(admin, failure):
    client, user, device = admin
    data = body(device)
    if failure == "password":
        data["password"] = "wrong"
    elif failure == "code":
        data["code"] = _hotp(device.secret, int(time.time() // 30) - 5)
    elif failure == "missing_device":
        device.delete()
    elif failure == "unconfirmed":
        device.is_confirmed = False
        device.save()
    else:
        # The request's cached user can be stale. The service must re-read it.
        get_user_model().objects.filter(pk=user.pk).update(
            **{"is_active" if failure == "disabled_user" else "is_superuser": False}
        )
    response = client.post(URL, data, format="json")
    assert response.status_code == 403, response.content
    assert not ProviderCredential.objects.exists()
    assert not ProviderCredentialProof.objects.exists()


def test_same_code_cannot_authorize_another_replacement(admin):
    client, _, device = admin
    data = body(device)
    assert client.post(URL, data, format="json").status_code == 200
    data["values"] = {"RESEND_API_KEY": "re_synthetic_12345678901234567890"}
    assert client.post(URL, data, format="json").status_code == 403
    assert not ProviderCredential.objects.filter(name="RESEND_API_KEY").exists()


@pytest.mark.parametrize(
    "values",
    [
        {},
        {"DATABASE_URL": SECRET},
        {"AFRICASTALKING_API_KEY": "short"},
        {"AFRICASTALKING_API_KEY": SECRET + "\n"},
        {"AFRICASTALKING_API_KEY": "x" * 513},
        [],
        None,
    ],
)
def test_malformed_or_unknown_credentials_are_refused_without_echoing_values(admin, values):
    client, _, device = admin
    response = client.post(URL, body(device, values=values), format="json")
    assert response.status_code == 400, response.content
    assert SECRET.encode() not in response.content
    assert not ProviderCredential.objects.exists()


def test_unknown_top_level_fields_and_non_object_payloads_are_refused(admin):
    client, _, device = admin
    assert client.post(URL, body(device, enabled=True), format="json").status_code == 400
    assert client.post(URL, [], format="json").status_code == 400


def test_replacements_are_throttled_before_password_verification(admin):
    client, _, device = admin
    data = body(device, password="incorrect")
    for _ in range(6):
        assert client.post(URL, data, format="json").status_code == 403
    with patch("django.contrib.auth.models.AbstractBaseUser.check_password") as verify:
        assert client.post(URL, data, format="json").status_code == 429
        verify.assert_not_called()


def test_encryption_misconfiguration_and_field_swapping_fail_closed(admin, settings):
    client, _, device = admin
    assert client.post(URL, body(device), format="json").status_code == 200
    good_key = settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY
    for bad in ("", "invalid", Fernet.generate_key().decode()):
        settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY = bad
        with pytest.raises(CredentialStoreUnavailable):
            credential("AFRICASTALKING_API_KEY")
    settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY = good_key
    row = ProviderCredential.objects.get()
    ProviderCredential.objects.create(name="RESEND_API_KEY", encrypted_value=row.encrypted_value)
    with pytest.raises(CredentialStoreUnavailable):
        credential("RESEND_API_KEY")


def test_missing_encryption_key_refuses_replacement_without_saving(admin, settings):
    client, _, device = admin
    settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY = ""
    response = client.post(URL, body(device), format="json")
    assert response.status_code == 503
    assert not ProviderCredential.objects.exists()


def test_encryption_rotation_uses_explicit_fallback_keys(admin, settings):
    client, _, device = admin
    assert client.post(URL, body(device), format="json").status_code == 200
    previous = settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY
    settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY = Fernet.generate_key().decode()
    settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY_FALLBACKS = [previous]
    assert credential("AFRICASTALKING_API_KEY") == SECRET


def test_no_cross_request_cache_and_bounded_reads(admin, django_assert_num_queries):
    client, _, device = admin
    assert client.post(URL, body(device), format="json").status_code == 200
    with django_assert_num_queries(1):
        assert credential("AFRICASTALKING_API_KEY") == SECRET
    ProviderCredential.objects.all().delete()
    with django_assert_num_queries(1):
        assert credential("AFRICASTALKING_API_KEY").startswith("synthetic-environment")


def test_private_tables_are_protected():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL RLS")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relname,relrowsecurity FROM pg_class WHERE relname IN "
            "('audit_providercredential','audit_providercredentialproof')"
        )
        assert dict(cursor.fetchall()) == {
            "audit_providercredential": True,
            "audit_providercredentialproof": True,
        }


@pytest.mark.django_db(transaction=True)
def test_concurrent_replacements_cannot_reuse_authenticator_code(admin):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locks")
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections

    _, user, device = admin
    barrier = Barrier(2)
    data = body(device)

    def attempt():
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user)
            barrier.wait(timeout=10)
            return client.post(URL, data, format="json").status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == [200, 403]
    assert ProviderCredential.objects.count() == 1
    assert AuditEvent.objects.filter(action="platform.provider_credentials_replaced").count() == 1
