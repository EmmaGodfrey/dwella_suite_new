"""Read-only Lenco connectivity check; collection flows are not enabled."""

import json
import urllib.error
import urllib.request


class LencoError(Exception):
    """A safe diagnostic that never includes provider payloads or credentials."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class LencoClient:
    # Only the selected environment is contacted. The sandbox v2 base remains
    # a setup probe; the live URL is documented in the v2 accounts reference.
    ACCOUNTS_URLS = {
        "sandbox": "https://sandbox.lenco.co/access/v2/accounts",
        "live": "https://api.lenco.co/access/v2/accounts",
    }
    MAX_RESPONSE_BYTES = 1024 * 1024

    def __init__(self, secret, *, environment):
        if environment not in self.ACCOUNTS_URLS:
            raise LencoError("Choose sandbox or live explicitly.")
        self.environment = environment
        if not isinstance(secret, str) or not 16 <= len(secret) <= 1024:
            raise LencoError("Configure the selected environment's secret/API token first.")
        if any(char.isspace() or ord(char) < 33 or ord(char) > 126 for char in secret):
            raise LencoError("The secret/API token has invalid characters.")
        self._secret = secret

    def check_accounts(self):
        request = urllib.request.Request(
            self.ACCOUNTS_URLS[self.environment],
            headers={
                "Authorization": f"Bearer {self._secret}",
                "Accept": "application/json",
                "User-Agent": "Dwella-Integration-Check/1.0",
            },
            method="GET",
        )
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=15) as response:
                if response.status != 200:
                    raise LencoError("Unexpected Lenco HTTP status.")
                if response.headers.get_content_type() != "application/json":
                    raise LencoError("Lenco returned a non-JSON response.")
                body = response.read(self.MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            raise LencoError(
                f"Lenco returned HTTP {code}; check selected token permissions and API access."
            ) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise LencoError("Lenco connection failed; check TLS/network availability.") from None
        if len(body) > self.MAX_RESPONSE_BYTES:
            raise LencoError("Lenco response exceeded the size limit.")
        try:
            payload = json.loads(body)
        except (ValueError, UnicodeError, RecursionError):
            raise LencoError("Lenco returned invalid JSON.") from None
        if (
            not isinstance(payload, dict)
            or payload.get("status") is not True
            or not isinstance(payload.get("data"), list)
            or not all(isinstance(account, dict) for account in payload["data"])
        ):
            raise LencoError("Lenco did not return a successful accounts response.")
        return len(payload["data"])
