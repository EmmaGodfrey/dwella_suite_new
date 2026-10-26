import base64
import hashlib
import json
import math
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

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite JSON number")
        return number

    return json.loads(body, parse_constant=reject_constant, parse_float=finite_float)


def cipher():
    if settings.LENCO_EVIDENCE_KEY:
        return MultiFernet(
            [
                Fernet(key)
                for key in [settings.LENCO_EVIDENCE_KEY, *settings.LENCO_EVIDENCE_KEY_FALLBACKS]
            ]
        )
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
    withdrawal=None,
    error="",
    request_payload=None,
    repeatable=False,
):
    """Store one provider exchange, or reuse the latest identical one.

    A repeatable read (a status poll, a ledger page) that returns exactly what
    the previous read of the same thing returned adds nothing to the evidence,
    so polling does not grow the table. Every change, error transition and
    every payout submission is still stored.
    """
    digest = hashlib.sha256(body).hexdigest()
    if repeatable and request_payload is None:
        latest = (
            Exchange.objects.filter(
                environment=environment,
                operation=operation,
                collection=collection,
                payout=payout,
                withdrawal=withdrawal,
            )
            .order_by("-id")
            .only("id", "body_sha256", "http_status", "error")
            .first()
        )
        if latest and (latest.body_sha256, latest.http_status, latest.error) == (
            digest,
            http_status,
            error,
        ):
            return latest
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
        withdrawal=withdrawal,
        http_status=http_status,
        body_sha256=digest,
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
