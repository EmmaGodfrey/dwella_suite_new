"""Small bounded JSON transport; provider credentials/payloads never enter logs."""

import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ProviderRejected(Exception):
    def __init__(self, code):
        self.code = str(code)[:80]
        super().__init__(self.code)


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
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read(262145))
    except HTTPError as error:
        # An explicit HTTP rejection is distinct from an uncertain network outcome.
        raise ProviderRejected(f"http_{error.code}") from None
