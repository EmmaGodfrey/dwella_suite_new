"""Deployment policy must permit hosted checkout without broad script access."""

import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest


@pytest.fixture
def policy():
    source = (Path(__file__).resolve().parents[3] / "frontend/nginx.conf").read_text()
    header = re.search(r'add_header Content-Security-Policy "([^"]+)"', source).group(1)
    return {parts[0]: parts[1:] for item in header.split(";") if (parts := item.split())}


@pytest.mark.parametrize("origin", ["https://pay.lenco.co", "https://pay.sandbox.lenco.co"])
def test_checkout_script_and_frame_origins_are_explicitly_allowed(policy, origin):
    assert origin in policy["script-src"]
    assert origin in policy["frame-src"]


def test_checkout_does_not_open_arbitrary_script_or_frame_sources(policy):
    for directive in ("script-src", "frame-src"):
        sources = policy[directive]
        assert not {
            "*",
            "https:",
            "http:",
            "data:",
            "blob:",
            "'unsafe-inline'",
            "'unsafe-eval'",
        }.intersection(sources)
        hosts = {urlsplit(source).hostname for source in sources if source.startswith("https://")}
        assert "pay.lenco.co.attacker.invalid" not in hosts
        assert hosts <= {"pay.lenco.co", "pay.sandbox.lenco.co", "handyai.wazabanda.dev"}
    assert policy["default-src"] == ["'self'"]
    assert policy["frame-ancestors"] == ["'none'"]
    assert policy["form-action"] == ["'self'"]
    assert policy["base-uri"] == ["'self'"]
