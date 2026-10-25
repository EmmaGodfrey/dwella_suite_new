import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.client import HTTPException

from django.conf import settings

from apps.integrations.lenco import LencoClient, _NoRedirect

from .evidence import record_exchange, strict_json

MAX_BODY = 1024 * 1024


@dataclass
class ProviderResult:
    payload: dict
    http_status: int | None
    error: str = ""


class Provider:
    """Bounded transport; a payout POST is never retried by the HTTP client."""

    def __init__(self, environment):
        if environment != settings.LENCO_ENVIRONMENT:
            raise ValueError("Cannot use another environment's credentials.")
        LencoClient(settings.LENCO_SECRET_KEY, environment=environment)
        self.environment = environment
        self.base = LencoClient.ACCOUNTS_URLS[environment].removesuffix("/accounts")

    def request(self, operation, *, collection, payout=None, payload=None):
        reference = payout.reference if payout else collection.reference
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,50}", reference):
            raise ValueError("Invalid provider reference.")
        paths = {
            "collection_status": f"/collections/status/{reference}",
            "payout_status": f"/transfers/status/{reference}",
            "payout_submit": "/transfers/mobile-money",
        }
        request = urllib.request.Request(
            self.base + paths[operation],
            method="POST" if operation == "payout_submit" else "GET",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Authorization": f"Bearer {settings.LENCO_SECRET_KEY}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        body, status, error, content_type = b"", None, "", ""
        try:
            with urllib.request.build_opener(_NoRedirect()).open(request, timeout=20) as response:
                status = response.status
                content_type = response.headers.get_content_type()
                body = response.read(MAX_BODY + 1)
        except urllib.error.HTTPError as exc:
            status = exc.code
            content_type = exc.headers.get_content_type()
            try:
                body = exc.read(MAX_BODY + 1)
            finally:
                exc.close()
            error = "http_error"
        except (urllib.error.URLError, OSError, TimeoutError, HTTPException):
            error = "network_error"
        if len(body) > MAX_BODY:
            body, error = body[:MAX_BODY], "response_too_large"
        parsed = {}
        try:
            candidate = strict_json(body)
            if isinstance(candidate, dict) and content_type == "application/json":
                parsed = candidate
            else:
                error = error or "invalid_response"
        except (ValueError, UnicodeError, RecursionError):
            error = error or "invalid_json"
        # Errors are persisted before domain validation, so a bad provider
        # response cannot disappear with a failed invoice transaction.
        record_exchange(
            environment=self.environment,
            operation=operation,
            body=body,
            collection=collection,
            payout=payout,
            http_status=status,
            error=error,
            request_payload=payload,
        )
        return ProviderResult(parsed, status, error)
