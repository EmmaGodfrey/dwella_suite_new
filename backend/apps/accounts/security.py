import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import Throttled

DISPOSABLE_EMAIL_DOMAINS = {
    "10minutemail.com",
    "guerrillamail.com",
    "mailinator.com",
    "tempmail.com",
    "temp-mail.org",
    "throwawaymail.com",
    "yopmail.com",
}


def normalize_email(email):
    return email.strip().lower()


def is_disposable_email(email):
    domain = normalize_email(email).split("@")[-1]
    return domain in DISPOSABLE_EMAIL_DOMAINS


def make_totp_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def totp_uri(secret, email, issuer="Dwella Suite"):
    label = quote(f"{issuer}:{email}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&digits=6&period=30"


def _hotp(secret, counter, digits=6):
    padded_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)


def verify_totp(secret, code, window=1):
    if not code or not str(code).isdigit():
        return False

    now_counter = int(time.time() // 30)
    code = str(code).strip()
    return any(
        hmac.compare_digest(_hotp(secret, now_counter + drift), code)
        for drift in range(-window, window + 1)
    )


def throttle_by_key(scope, identifier, limit, timeout):
    cache_key = f"throttle:{scope}:{identifier}"
    attempts = cache.get(cache_key, 0)
    if attempts >= limit:
        raise Throttled(detail="Too many attempts. Please try again later.")
    cache.set(cache_key, attempts + 1, timeout)


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def frontend_reset_url(uid, token):
    return f"{settings.FRONTEND_URL.rstrip('/')}/login?reset_uid={uid}&reset_token={token}"
