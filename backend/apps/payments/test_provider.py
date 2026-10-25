from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from .provider import Provider


@pytest.mark.parametrize("operation", ["collection_status", "payout_status", "payout_submit"])
def test_transport_is_bounded_audited_and_never_retries(operation, settings):
    settings.LENCO_ENVIRONMENT = "sandbox"
    settings.LENCO_SECRET_KEY = "fake-provider-token-only-for-tests"
    row = SimpleNamespace(reference="rent-test")
    with (
        patch("apps.payments.provider.urllib.request.build_opener") as build,
        patch("apps.payments.provider.record_exchange") as evidence,
    ):
        build.return_value.open.side_effect = TimeoutError("details must not escape")
        result = Provider("sandbox").request(
            operation,
            collection=row,
            payout=row if operation != "collection_status" else None,
            payload={"amount": 1} if operation == "payout_submit" else None,
        )
    assert result.error == "network_error"
    assert build.return_value.open.call_count == 1
    assert build.return_value.open.call_args.kwargs["timeout"] == 20
    assert evidence.call_args.kwargs["error"] == "network_error"
    assert evidence.call_args.kwargs["body"] == b""
    assert "Authorization" not in evidence.call_args.kwargs


def test_unsupported_environment_does_not_send_keys(settings):
    settings.LENCO_ENVIRONMENT = "sandbox"
    with patch("apps.payments.provider.urllib.request.build_opener") as build:
        with pytest.raises(ValueError):
            Provider("live")
        build.assert_not_called()


def test_failed_http_response_body_timeout_still_creates_evidence(settings):
    import urllib.error
    from email.message import Message

    settings.LENCO_ENVIRONMENT = "sandbox"
    settings.LENCO_SECRET_KEY = "fake-provider-token-only-for-tests"
    headers = Message()
    headers["Content-Type"] = "application/json"
    body = Mock()
    body.read.side_effect = TimeoutError("not a safe diagnostic")
    error = urllib.error.HTTPError("https://sandbox.lenco.co", 503, "error", headers, body)
    with (
        patch("apps.payments.provider.urllib.request.build_opener") as build,
        patch("apps.payments.provider.record_exchange") as evidence,
    ):
        build.return_value.open.side_effect = error
        result = Provider("sandbox").request("accounts")
    assert result.http_status == 503 and result.error == "incomplete_response"
    assert evidence.call_args.kwargs["http_status"] == 503
    assert evidence.call_args.kwargs["error"] == "incomplete_response"
