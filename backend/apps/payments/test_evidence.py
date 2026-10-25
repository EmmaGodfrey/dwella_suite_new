import hashlib
import json

import pytest

from .evidence import read_exchange, record_exchange


@pytest.mark.django_db
def test_response_evidence_is_encrypted_redacted_and_immutable(settings):
    settings.LENCO_SECRET_KEY = "secret-for-evidence-test"
    settings.LENCO_PUBLIC_KEY = "public-for-evidence-test"
    raw = json.dumps(
        {
            "reasonForFailure": "declined",
            "Authorization": "Bearer leaked",
            "secret_key": settings.LENCO_SECRET_KEY,
            "cardDetails": {"pan": "4111111111111111", "cvv": "123"},
        }
    ).encode()
    row = record_exchange(environment="sandbox", operation="test", body=raw, http_status=400)
    assert row.body_sha256 == hashlib.sha256(raw).hexdigest()
    assert b"declined" not in bytes(row.encrypted_payload)
    decoded = read_exchange(row)["response"]
    assert decoded["reasonForFailure"] == "declined"
    assert settings.LENCO_SECRET_KEY not in json.dumps(decoded)
    assert decoded["cardDetails"]["cvv"] == "[redacted]"
    with pytest.raises(ValueError):
        row.save()
    with pytest.raises(ValueError):
        row.delete()


@pytest.mark.django_db
def test_evidence_survives_secret_key_rotation(settings):
    settings.SECRET_KEY = "old-encryption-key"
    row = record_exchange(environment="sandbox", operation="test", body=b'{"status":false}')
    settings.SECRET_KEY_FALLBACKS = [settings.SECRET_KEY]
    settings.SECRET_KEY = "new-encryption-key"
    assert read_exchange(row)["response"]["status"] is False
