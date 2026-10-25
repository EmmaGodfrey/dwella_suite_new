import base64
import hashlib
import json
import re

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.utils.crypto import salted_hmac

from .models import Exchange

SENSITIVE = {
    "authorization",
    "secret",
    "secretkey",
    "apikey",
    "token",
    "accesstoken",
    "password",
    "pan",
    "cardnumber",
    "cvv",
    "cvc",
    "pin",
    "otp",
    "publickey",
    "apisecretkey",
    "apitoken",
}


def strict_json(body):
    def reject_constant(value):
        raise ValueError("Non-finite JSON number")

    return json.loads(body, parse_constant=reject_constant)


def cipher():
    return MultiFernet(
        [
            Fernet(
                base64.urlsafe_b64encode(
                    salted_hmac(
                        "dwella.lenco.evidence.v1", "payload", secret=key, algorithm="sha256"
                    ).digest()
                )
            )
            for key in [settings.SECRET_KEY, *settings.SECRET_KEY_FALLBACKS]
        ]
    )


def redact(value, depth=0):
    if depth > 25:
        return "[nested content omitted]"
    if isinstance(value, dict):
        return {
            key: "[redacted]"
            if re.sub(r"[^a-z]", "", key.lower()) in SENSITIVE
            else redact(item, depth + 1)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, depth + 1) for item in value]
    if isinstance(value, str):
        for secret in (settings.LENCO_SECRET_KEY, settings.LENCO_PUBLIC_KEY):
            if secret:
                value = value.replace(secret, "[redacted]")
        value = re.sub(r"(?i)bearer\s+\S+", "Bearer [redacted]", value)
        return re.sub(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)", "[redacted digits]", value)
    return value


def record_exchange(
    *,
    environment,
    operation,
    body,
    http_status=None,
    collection=None,
    payout=None,
    error="",
    request_payload=None,
):
    try:
        payload = strict_json(body)
    except (ValueError, UnicodeError, RecursionError):
        # Preserve the digest and a safe diagnostic; arbitrary HTML/text may
        # contain credentials or card information outside structured fields.
        payload = {"non_json": True, "bytes": len(body)}
    return Exchange.objects.create(
        environment=environment,
        operation=operation,
        collection=collection,
        payout=payout,
        http_status=http_status,
        body_sha256=hashlib.sha256(body).hexdigest(),
        error=error,
        encrypted_payload=cipher().encrypt(
            json.dumps(
                redact(
                    {
                        "request": request_payload,
                        "response": payload,
                    }
                ),
                allow_nan=False,
            ).encode()
        ),
    )


def read_exchange(exchange):
    return json.loads(cipher().decrypt(bytes(exchange.encrypted_payload)))
