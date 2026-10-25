import hashlib
import json

import pytest

from .evidence import read_exchange, record_exchange, strict_json


@pytest.mark.parametrize("body", [b'{"amount":NaN}', b'{"amount":1e999}'])
def test_nonfinite_json_numbers_are_rejected_before_encryption(body):
    with pytest.raises(ValueError):
        strict_json(body)


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
    settings.LENCO_EVIDENCE_KEY = ""
    settings.SECRET_KEY = "old-encryption-key"
    row = record_exchange(environment="sandbox", operation="test", body=b'{"status":false}')
    settings.SECRET_KEY_FALLBACKS = [settings.SECRET_KEY]
    settings.SECRET_KEY = "new-encryption-key"
    assert read_exchange(row)["response"]["status"] is False


@pytest.mark.django_db
def test_dedicated_evidence_key_rotation_preserves_retained_history(settings):
    from cryptography.fernet import Fernet

    old_key = Fernet.generate_key().decode()
    settings.LENCO_EVIDENCE_KEY = old_key
    row = record_exchange(environment="sandbox", operation="test", body=b'{"status":false}')
    settings.LENCO_EVIDENCE_KEY = Fernet.generate_key().decode()
    settings.LENCO_EVIDENCE_KEY_FALLBACKS = [old_key]
    assert read_exchange(row)["response"]["status"] is False


@pytest.mark.django_db
def test_repeated_identical_reads_reuse_one_record_but_changes_are_kept():
    from .models import Exchange

    def read(body, **kwargs):
        return record_exchange(
            environment="sandbox", operation="poll", body=body, repeatable=True, **kwargs
        )

    pending = b'{"status":true,"data":{"status":"pending"}}'
    first = read(pending, http_status=200)
    assert read(pending, http_status=200).pk == first.pk
    assert Exchange.objects.count() == 1
    # A changed answer, an error and the return to the old answer are all kept.
    read(b'{"status":true,"data":{"status":"successful"}}', http_status=200)
    read(b"", error="network_error")
    assert read(b"", error="network_error").pk == Exchange.objects.order_by("-id").first().pk
    read(pending, http_status=200)
    assert Exchange.objects.count() == 4
    # Writes and other operations never reuse a read.
    record_exchange(environment="sandbox", operation="poll", body=pending, http_status=200)
    record_exchange(environment="sandbox", operation="other", body=pending, repeatable=True)
    assert Exchange.objects.count() == 6
