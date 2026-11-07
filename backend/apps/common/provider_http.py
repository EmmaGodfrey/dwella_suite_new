"""Small bounded JSON transport; provider credentials/payloads never enter logs."""

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ProviderRejected(Exception):
    def __init__(self, code):
        self.code = str(code)[:80]
        super().__init__(self.code)


class _NoRedirect(HTTPRedirectHandler):
    # Following a redirect would forward the bearer token to whichever host was named.
    def redirect_request(self, *args, **kwargs):
        return None


_no_redirect = build_opener(_NoRedirect)


def get_bytes(url, headers, limit):
    request = Request(url, headers=headers, method="GET")
    try:
        with _no_redirect.open(request, timeout=10) as response:
            raw = response.read(limit + 1)
    except HTTPError as error:
        raise ProviderRejected(f"http_{error.code}") from None
    if len(raw) > limit:
        raise ProviderRejected("too_large")
    return raw


def get_json(url, headers):
    return json.loads(get_bytes(url, headers, 262144))


def post_json(url, payload, headers):
    return post_request(url, json.dumps(payload).encode(), "application/json", headers)


def post_form(url, payload, headers):
    return post_request(
        url, urlencode(payload).encode(), "application/x-www-form-urlencoded", headers
    )


def post_request(url, data, content_type, headers):
    request = Request(
        url,
        data=data,
        headers={"Content-Type": content_type, **headers},
        method="POST",
    )
    try:
        with _no_redirect.open(request, timeout=10) as response:
            return json.loads(response.read(262145))
    except HTTPError as error:
        # An explicit HTTP rejection is distinct from an uncertain network outcome.
        raise ProviderRejected(f"http_{error.code}") from None
