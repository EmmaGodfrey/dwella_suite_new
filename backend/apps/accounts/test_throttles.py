import time
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.core.signing import TimestampSigner
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient, APIRequestFactory

from .security import get_client_ip
from .throttles import (
    AtomicWindowThrottle,
    InvitationTokenThrottle,
    LoginAccountThrottle,
    LoginIPThrottle,
    PasswordResetConfirmThrottle,
    TwoFactorAccountThrottle,
)

LOGIN = "/api/v1/accounts/login/"
RESET = "/api/v1/accounts/password-reset/"
PREVIEW = "/api/v1/accounts/invitations/preview/"


@pytest.fixture(autouse=True)
def isolated_cache(settings, monkeypatch):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    monkeypatch.setattr(AtomicWindowThrottle, "timer", staticmethod(lambda: 1800000001.0))
    cache.clear()
    yield
    cache.clear()


def set_rates(settings, **rates):
    config = deepcopy(settings.REST_FRAMEWORK)
    config["DEFAULT_THROTTLE_RATES"].update(rates)
    settings.REST_FRAMEWORK = config


def request(data, **meta):
    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request

    return Request(
        APIRequestFactory().post("/", data, format="json", **meta), parsers=[JSONParser()]
    )


@pytest.mark.django_db
def test_fifteen_accounts_can_login_from_one_shared_ip(settings):
    set_rates(settings, anon="1/hour", user="1/hour")
    encoded = make_password("OfficePassphrase123!")
    users = [
        get_user_model()(
            username=f"tenant{i}@example.com", email=f"tenant{i}@example.com", password=encoded
        )
        for i in range(15)
    ]
    get_user_model().objects.bulk_create(users)
    client = APIClient(REMOTE_ADDR="198.51.100.1")
    for user in users:
        response = client.post(LOGIN, {"email": user.email, "password": "OfficePassphrase123!"})
        assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize("exists", [False, True])
def test_account_limit_is_normalized_and_does_not_depend_on_existence(exists):
    if exists:
        get_user_model().objects.create_user(
            username="one", email="one@example.com", password="Correct123!"
        )
    for i in range(8):
        client = APIClient(REMOTE_ADDR=f"198.51.100.{i + 1}")
        assert (
            client.post(LOGIN, {"email": " ONE@EXAMPLE.COM ", "password": "wrong"}).status_code
            == 400
        )
    response = APIClient(REMOTE_ADDR="203.0.113.1").post(
        LOGIN, {"email": "one@example.com", "password": "wrong"}
    )
    assert response.status_code == 429
    assert int(response["Retry-After"]) > 0
    assert "one@example.com" not in str(response.data)


@pytest.mark.django_db
def test_login_ip_ceiling_still_blocks_many_different_accounts():
    client = APIClient(REMOTE_ADDR="198.51.100.1")
    for i in range(60):
        assert (
            client.post(LOGIN, {"email": f"absent{i}@example.com", "password": "wrong"}).status_code
            == 400
        )
    assert (
        client.post(LOGIN, {"email": "another@example.com", "password": "wrong"}).status_code == 429
    )


@pytest.mark.django_db
def test_password_resets_share_ip_but_have_separate_account_budgets(settings):
    set_rates(settings, anon="1/hour", user="1/hour")
    client = APIClient(REMOTE_ADDR="198.51.100.1")
    for i in range(15):
        response = client.post(RESET, {"email": f"absent{i}@example.com"})
        assert response.status_code == 202
        assert "If that email exists" in response.data["detail"]
    for _ in range(2):
        assert client.post(RESET, {"email": " ABSENT0@example.com "}).status_code == 202
    assert client.post(RESET, {"email": "absent0@example.com"}).status_code == 429


@pytest.mark.django_db
def test_reset_ip_ceiling_and_stale_auth_token(settings):
    set_rates(settings, password_reset_ip="2/minute")
    client = APIClient(HTTP_AUTHORIZATION="Token revoked", REMOTE_ADDR="198.51.100.1")
    assert client.post(RESET, {"email": "one@example.com"}).status_code == 202
    assert client.post(RESET, {"email": "two@example.com"}).status_code == 202
    assert client.post(RESET, {"email": "three@example.com"}).status_code == 429


@pytest.mark.django_db
def test_invitation_links_do_not_share_the_old_twenty_per_hour_budget(settings):
    set_rates(settings, anon="1/hour", user="1/hour")
    client = APIClient(REMOTE_ADDR="198.51.100.1")
    for i in range(30):
        assert client.post(PREVIEW, {"token": f"{i:043}"}).status_code == 400
    for _ in range(19):
        assert client.post(PREVIEW, {"token": "x" * 43}).status_code == 400
    assert client.post(PREVIEW, {"token": "x" * 43}).status_code == 400
    assert client.post(PREVIEW, {"token": "x" * 43}).status_code == 429


@pytest.mark.django_db
def test_invitation_ip_limit_applies_even_to_authenticated_clients(settings):
    set_rates(settings, tenant_invitation_ip="2/minute")
    user = get_user_model().objects.create_user(username="one", email="one@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    for i in range(2):
        assert client.post(PREVIEW, {"token": f"{i:043}"}).status_code == 400
    assert client.post(PREVIEW, {"token": "x" * 43}).status_code == 429


def test_two_factor_uses_signed_user_identity_not_changeable_challenge(settings, monkeypatch):
    set_rates(settings, two_factor="2/minute")
    signer = TimestampSigner(salt="accounts.two_factor.challenge")
    tokens = []
    for offset in [0, 1]:
        # A new timestamp/signature for the same account must retain its budget.
        timestamp = str(int(time.time()) - offset)
        monkeypatch.setattr(signer, "timestamp", lambda value=timestamp: value)
        token = signer.sign("42")
        tokens.append(token)
        assert TwoFactorAccountThrottle().allow_request(request({"challenge_token": token}), None)
    assert tokens[0] != tokens[1]
    assert not TwoFactorAccountThrottle().allow_request(
        request({"challenge_token": signer.sign("42")}), None
    )
    assert TwoFactorAccountThrottle().allow_request(
        request({"challenge_token": signer.sign("43")}), None
    )


@pytest.mark.django_db
def test_two_factor_many_accounts_share_ip_and_account_retries_are_limited(settings):
    set_rates(settings, anon="1/hour", user="1/hour", two_factor="2/minute")
    signer = TimestampSigner(salt="accounts.two_factor.challenge")
    client = APIClient()
    for i in range(15):
        assert (
            client.post(
                LOGIN + "2fa/", {"challenge_token": signer.sign(str(i + 1)), "code": "000000"}
            ).status_code
            == 400
        )
    token = signer.sign("1")
    assert (
        client.post(LOGIN + "2fa/", {"challenge_token": token, "code": "000000"}).status_code == 400
    )
    assert (
        client.post(LOGIN + "2fa/", {"challenge_token": token, "code": "000000"}).status_code == 429
    )


@pytest.mark.parametrize(
    "throttle", [LoginAccountThrottle, LoginIPThrottle, InvitationTokenThrottle]
)
@pytest.mark.parametrize("payload", [[], None, {"email": []}, {"email": "x" * 2000}])
def test_malformed_payloads_have_bounded_private_keys(throttle, payload):
    key = throttle().get_cache_key(request(payload), None)
    assert len(key) < 150
    assert "x" * 100 not in key


def test_cache_key_never_contains_email_or_link():
    email = "private@example.com"
    assert email not in LoginAccountThrottle().get_cache_key(request({"email": email}), None)
    token = "secret-invitation-token"
    assert token not in InvitationTokenThrottle().get_cache_key(request({"token": token}), None)


def test_whitespace_cannot_move_a_valid_email_out_of_its_account_budget():
    normal = LoginAccountThrottle().get_cache_key(request({"email": "one@example.com"}), None)
    padded = LoginAccountThrottle().get_cache_key(
        request({"email": " " * 1000 + "ONE@EXAMPLE.COM" + " " * 1000}), None
    )
    assert normal == padded


def test_reset_confirmation_uid_aliases_share_a_budget():
    a = PasswordResetConfirmThrottle().get_cache_key(
        request({"uid": urlsafe_base64_encode(b"42")}), None
    )
    b = PasswordResetConfirmThrottle().get_cache_key(
        request({"uid": urlsafe_base64_encode(b"0042")}), None
    )
    assert a == b


@pytest.mark.parametrize("count", [0, 1, 2])
def test_proxy_count_matches_audit_and_cannot_be_bypassed_by_prefix(settings, count):
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": count}
    suffix = ", 198.51.100.9" if count == 1 else ", 198.51.100.9, 10.0.0.2"
    a = request({}, REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.1" + suffix)
    b = request({}, REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.2" + suffix)
    assert LoginIPThrottle().get_cache_key(a, None) == LoginIPThrottle().get_cache_key(b, None)
    assert get_client_ip(a) == ("10.0.0.1" if count == 0 else "198.51.100.9")


def test_atomic_account_counter_has_no_thread_overshoot(settings, monkeypatch):
    set_rates(settings, login="8/minute")
    monkeypatch.setattr(LoginAccountThrottle, "timer", staticmethod(lambda: 1234567.0))

    def attempt(_):
        return LoginAccountThrottle().allow_request(request({"email": "one@example.com"}), None)

    with ThreadPoolExecutor(max_workers=16) as pool:
        assert sum(pool.map(attempt, range(64))) == 8


def test_counter_recovers_from_eviction_without_server_error(monkeypatch):
    throttle = LoginAccountThrottle()
    monkeypatch.setattr(throttle.cache, "add", lambda *args: False)
    monkeypatch.setattr(throttle.cache, "incr", lambda *args: (_ for _ in ()).throw(ValueError()))
    assert not throttle.allow_request(request({"email": "one@example.com"}), None)
    assert throttle.wait() > 0


def test_fixed_window_expires_and_zero_rate_fails_closed(settings, monkeypatch):
    set_rates(settings, login="1/minute")
    assert LoginAccountThrottle().allow_request(request({"email": "one@example.com"}), None)
    assert not LoginAccountThrottle().allow_request(request({"email": "one@example.com"}), None)
    monkeypatch.setattr(LoginAccountThrottle, "timer", staticmethod(lambda: 1800000061.0))
    assert LoginAccountThrottle().allow_request(request({"email": "one@example.com"}), None)
    set_rates(settings, login="0/minute")
    assert not LoginAccountThrottle().allow_request(request({"email": "other@example.com"}), None)


def test_incremented_counter_always_has_a_bounded_ttl(monkeypatch):
    from unittest.mock import Mock

    throttle = LoginAccountThrottle()
    backend = Mock()
    backend.add.return_value = False
    backend.incr.return_value = 2
    throttle.cache = backend
    assert throttle.allow_request(request({"email": "one@example.com"}), None)
    key, timeout = backend.touch.call_args.args
    assert "one@example.com" not in key
    assert 1 <= timeout <= 61
