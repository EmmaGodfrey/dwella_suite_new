import io
import json
import os
import urllib.error
from email.message import Message
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from .lenco import LencoClient, LencoError, _NoRedirect

TOKEN = "sandbox-test-token-placeholder"


def response(payload=None, *, body=None, content_type="application/json"):
    result = Mock()
    result.status = 200
    result.headers = Message()
    result.headers["Content-Type"] = content_type
    result.read.return_value = body if body is not None else json.dumps(payload).encode()
    result.__enter__ = Mock(return_value=result)
    result.__exit__ = Mock(return_value=False)
    return result


@patch("apps.integrations.lenco.urllib.request.build_opener")
def test_sandbox_check_is_read_only_and_uses_only_sandbox(build):
    build.return_value.open.return_value = response({"status": True, "data": [{"id": "private"}]})
    assert LencoClient(TOKEN, environment="sandbox").check_accounts() == 1
    request = build.return_value.open.call_args.args[0]
    assert request.full_url == "https://sandbox.lenco.co/access/v2/accounts"
    assert request.get_method() == "GET"
    assert request.data is None
    assert request.get_header("Authorization") == f"Bearer {TOKEN}"
    assert build.return_value.open.call_args.kwargs["timeout"] == 15
    assert isinstance(build.call_args.args[0], _NoRedirect)


@pytest.mark.parametrize("token", ["", "short", "x" * 1025, "x" * 20 + "\r\nInjected: true"])
def test_invalid_tokens_never_make_requests(token):
    with patch("apps.integrations.lenco.urllib.request.build_opener") as build:
        with pytest.raises(LencoError):
            LencoClient(token, environment="sandbox")
        build.assert_not_called()


@pytest.mark.parametrize("code", [301, 302, 307, 401, 403, 429, 500])
@patch("apps.integrations.lenco.urllib.request.build_opener")
def test_http_errors_redact_provider_body_and_token(build, code):
    build.return_value.open.side_effect = urllib.error.HTTPError(
        "https://sandbox.lenco.co/access/v2/accounts", code, TOKEN, {}, io.BytesIO(TOKEN.encode())
    )
    with pytest.raises(LencoError) as caught:
        LencoClient(TOKEN, environment="sandbox").check_accounts()
    assert str(code) in str(caught.value)
    assert TOKEN not in str(caught.value)
    assert build.return_value.open.call_count == 1


def test_redirect_handler_never_forwards_credentials():
    assert _NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.test") is None


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"status": False, "data": []},
        {"status": True, "data": {}},
        {"status": True, "data": [None]},
    ],
)
@patch("apps.integrations.lenco.urllib.request.build_opener")
def test_invalid_provider_schema(build, payload):
    build.return_value.open.return_value = response(payload)
    with pytest.raises(LencoError):
        LencoClient(TOKEN, environment="sandbox").check_accounts()


@pytest.mark.parametrize(
    "reply",
    [
        response(body=b"<html>"),
        response(body=b"{}", content_type="text/html"),
        response(body=b"x" * (1024 * 1024 + 1)),
    ],
)
@patch("apps.integrations.lenco.urllib.request.build_opener")
def test_invalid_or_oversized_body(build, reply):
    build.return_value.open.return_value = reply
    with pytest.raises(LencoError):
        LencoClient(TOKEN, environment="sandbox").check_accounts()


@pytest.mark.parametrize("error", [urllib.error.URLError(TOKEN), TimeoutError(TOKEN)])
@patch("apps.integrations.lenco.urllib.request.build_opener")
def test_network_failure_is_redacted(build, error):
    build.return_value.open.side_effect = error
    with pytest.raises(LencoError) as caught:
        LencoClient(TOKEN, environment="sandbox").check_accounts()
    assert TOKEN not in str(caught.value)


@patch.dict(os.environ, {"LENCO_ENVIRONMENT": "production"})
@patch("apps.integrations.management.commands.check_lenco.LencoClient")
def test_command_rejects_environment_mismatch(client):
    with pytest.raises(CommandError, match="must match LENCO_ENVIRONMENT"):
        call_command("check_lenco", environment="sandbox")
    client.assert_not_called()


@patch.dict(os.environ, {"LENCO_ENVIRONMENT": "sandbox", "LENCO_SANDBOX_SECRET_KEY": TOKEN})
@patch("apps.integrations.management.commands.check_lenco.LencoClient")
def test_command_prints_only_safe_summary(client):
    client.return_value.check_accounts.return_value = 2
    output = io.StringIO()
    call_command("check_lenco", environment="sandbox", stdout=output)
    assert "authentication succeeded" in output.getvalue()
    assert TOKEN not in output.getvalue()


@patch("apps.integrations.lenco.urllib.request.build_opener")
def test_live_check_uses_live_url_without_fallback(build):
    build.return_value.open.return_value = response({"status": True, "data": []})
    assert LencoClient(TOKEN, environment="live").check_accounts() == 0
    request = build.return_value.open.call_args.args[0]
    assert request.full_url == "https://api.lenco.co/access/v2/accounts"
    assert request.get_method() == "GET"
    assert build.return_value.open.call_count == 1


def test_unknown_environment_is_rejected():
    with pytest.raises(LencoError, match="explicitly"):
        LencoClient(TOKEN, environment="unexpected")


@patch.dict(os.environ, {"LENCO_ENVIRONMENT": "live", "LENCO_LIVE_SECRET_KEY": TOKEN})
@patch("apps.integrations.management.commands.check_lenco.LencoClient")
def test_live_command_selects_only_live_secret(client):
    client.return_value.check_accounts.return_value = 1
    call_command("check_lenco", environment="live", stdout=io.StringIO())
    client.assert_called_once_with(TOKEN, environment="live")
