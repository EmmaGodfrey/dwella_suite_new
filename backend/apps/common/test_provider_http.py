"""Credential-bearing provider POSTs must never follow redirects or retry."""

from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from .provider_http import ProviderRejected, _NoRedirect, post_json


def test_provider_post_uses_no_redirect_opener_and_does_not_retry():
    with patch("apps.common.provider_http._no_redirect.open") as send:
        send.side_effect = HTTPError("https://provider.invalid", 302, "redirect", {}, None)
        with pytest.raises(ProviderRejected, match="http_302"):
            post_json(
                "https://provider.invalid",
                {"code": "synthetic"},
                {"Authorization": "Bearer synthetic"},
            )
    assert send.call_count == 1
    assert send.call_args.kwargs["timeout"] == 10
    request = send.call_args.args[0]
    assert request.get_method() == "POST"
    assert (
        _NoRedirect().redirect_request(request, None, 302, "", {}, "https://other.invalid") is None
    )
