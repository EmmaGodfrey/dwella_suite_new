"""Account/link limits plus independent ceilings for shared public networks."""

import math
from collections.abc import Mapping

from django.core.signing import BadSignature, TimestampSigner
from django.utils.crypto import salted_hmac
from django.utils.http import urlsafe_base64_decode
from rest_framework.settings import api_settings
from rest_framework.throttling import SimpleRateThrottle


def body_string(request, field, maximum=320):
    data = request.data
    value = data.get(field) if isinstance(data, Mapping) else None
    value = value.strip() if isinstance(value, str) else ""
    return value if len(value) <= maximum else ""


class AtomicWindowThrottle(SimpleRateThrottle):
    """Atomic cache counters avoid read/modify/write races between gunicorn threads.

    Fixed windows have bounded TTLs and may allow twice the limit across a window
    boundary. Production requires a shared cache with atomic add/incr (Redis).
    """

    def get_rate(self):
        return api_settings.DEFAULT_THROTTLE_RATES[self.scope]

    def identifier(self, request):
        return self.get_ident(request)

    def get_cache_key(self, request, view):
        identifier = self.identifier(request) or "unknown"
        digest = salted_hmac("accounts.throttle", str(identifier), algorithm="sha256").hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": digest}

    def allow_request(self, request, view):
        if self.rate is None:
            return True
        now = self.timer()
        window = int(now // self.duration)
        self.remaining = self.duration - now % self.duration
        key = f"{self.get_cache_key(request, view)}:{window}"
        timeout = math.ceil(self.remaining) + 1
        if self.cache.add(key, 1, timeout):
            return self.num_requests >= 1
        try:
            count = self.cache.incr(key)
        except ValueError:
            # An eviction/expiry between add and incr must not turn into a 500.
            if self.cache.add(key, 1, timeout):
                return self.num_requests >= 1
            try:
                count = self.cache.incr(key)
            except ValueError:
                return False
        # Redis may recreate a key if it expires between Django's exists/incr
        # calls. Reapply the same window deadline so no counter lives forever.
        self.cache.touch(key, timeout)
        return count <= self.num_requests

    def wait(self):
        return self.remaining


class LoginIPThrottle(AtomicWindowThrottle):
    scope = "login_ip"


class LoginAccountThrottle(AtomicWindowThrottle):
    scope = "login"

    def identifier(self, request):
        email = body_string(request, "email").lower()
        return f"email:{email}" if email else f"malformed:{self.get_ident(request)}"


class PasswordResetIPThrottle(AtomicWindowThrottle):
    scope = "password_reset_ip"


class PasswordResetAccountThrottle(LoginAccountThrottle):
    scope = "password_reset"


class PasswordResetConfirmThrottle(AtomicWindowThrottle):
    scope = "password_reset_confirm"

    def identifier(self, request):
        try:
            uid = int(urlsafe_base64_decode(body_string(request, "uid")))
            if uid > 0:
                return f"user:{uid}"
        except (ValueError, TypeError, OverflowError):
            pass
        return f"malformed:{self.get_ident(request)}"


class TwoFactorIPThrottle(AtomicWindowThrottle):
    scope = "two_factor_ip"


class TwoFactorAccountThrottle(AtomicWindowThrottle):
    scope = "two_factor"

    def identifier(self, request):
        try:
            uid = TimestampSigner(salt="accounts.two_factor.challenge").unsign(
                body_string(request, "challenge_token", maximum=1024), max_age=300
            )
            return f"user:{uid}"
        except BadSignature:
            return f"malformed:{self.get_ident(request)}"


class InvitationIPThrottle(AtomicWindowThrottle):
    scope = "tenant_invitation_ip"


class InvitationTokenThrottle(AtomicWindowThrottle):
    scope = "tenant_invitation_token"

    def identifier(self, request):
        token = body_string(request, "token", maximum=100)
        return f"link:{token}" if token else f"malformed:{self.get_ident(request)}"
