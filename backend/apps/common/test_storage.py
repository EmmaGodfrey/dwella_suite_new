import io
from unittest.mock import PropertyMock, patch
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from config.storage import storage_settings


@pytest.fixture
def s3_env(monkeypatch):
    for key, value in {
        "STORAGE_BACKEND": "s3", "STORAGE_S3_BUCKET": "dwella-test",
        "STORAGE_S3_ACCESS_KEY": "test-access-key", "STORAGE_S3_SECRET_KEY": "test-secret",
        "STORAGE_S3_ENDPOINT_URL": "https://example.r2.cloudflarestorage.com",
        "STORAGE_S3_REGION": "auto", "STORAGE_S3_URL_TTL": "900",
    }.items():
        monkeypatch.setenv(key, value)


def test_local_storage_remains_default(monkeypatch):
    monkeypatch.delenv("STORAGE_BACKEND", raising=False)
    assert storage_settings()["default"]["BACKEND"].endswith("FileSystemStorage")


@pytest.mark.parametrize("key,value", [
    ("STORAGE_BACKEND", "typo"), ("STORAGE_S3_BUCKET", ""),
    ("STORAGE_S3_BUCKET", "../wrong"), ("STORAGE_S3_ACCESS_KEY", ""),
    ("STORAGE_S3_SECRET_KEY", ""), ("STORAGE_S3_ENDPOINT_URL", "http://insecure.test"),
    ("STORAGE_S3_ENDPOINT_URL", "https://key:secret@example.test"),
    ("STORAGE_S3_ENDPOINT_URL", "https://example.test/bucket"),
    ("STORAGE_S3_ENDPOINT_URL", "https://example.test?token=secret"),
    ("STORAGE_S3_URL_TTL", "0"), ("STORAGE_S3_URL_TTL", "3601"),
    ("STORAGE_S3_URL_TTL", "invalid"),
])
def test_object_storage_rejects_incomplete_or_unsafe_config(s3_env, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    with pytest.raises(ImproperlyConfigured):
        storage_settings()


def test_s3_urls_are_private_expiring_and_preserve_static_storage(s3_env):
    from storages.backends.s3 import S3Storage

    config = storage_settings()
    storage = S3Storage(**config["default"]["OPTIONS"])
    url = storage.url("profiles/avatars/photo.png")
    parsed = urlsplit(url)
    query = parse_qs(parsed.query)
    assert parsed.hostname == "example.r2.cloudflarestorage.com"
    assert parsed.path == "/dwella-test/profiles/avatars/photo.png"
    assert query["X-Amz-Expires"] == ["900"]
    assert "X-Amz-Signature" in query
    assert storage.default_acl is None
    assert storage.file_overwrite is False
    assert storage.custom_domain is None
    assert config["staticfiles"]["BACKEND"].endswith("StaticFilesStorage")


def test_s3_upload_sets_no_public_acl_or_overwrite(s3_env):
    from storages.backends.s3 import S3Storage

    storage = S3Storage(**storage_settings()["default"]["OPTIONS"])
    with patch.object(S3Storage, "connection", new_callable=PropertyMock) as prop:
        connection = prop.return_value
        storage._save("test.png", ContentFile(b"image"))
    upload = connection.Bucket.return_value.Object.return_value.upload_fileobj
    assert "ACL" not in upload.call_args.kwargs["ExtraArgs"]
    assert upload.call_args.kwargs["ExtraArgs"]["CacheControl"] == "private, max-age=0, no-store"


def test_probe_refuses_local_storage():
    with override_settings(STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    }), pytest.raises(CommandError, match="disabled"):
        call_command("check_object_storage")


def test_probe_configuration_only_never_accesses_remote(s3_env):
    with override_settings(STORAGES=storage_settings()), patch(
        "apps.common.management.commands.check_object_storage.default_storage"
    ) as storage:
        output = io.StringIO()
        call_command("check_object_storage", stdout=output)
        assert "No remote requests" in output.getvalue()
        assert not storage.mock_calls


@pytest.mark.parametrize("read_fails", [False, True])
def test_probe_cleans_up_its_own_file_even_on_read_failure(s3_env, tmp_path, read_fails):
    storage = FileSystemStorage(location=tmp_path)
    original = storage.save("customer.txt", ContentFile(b"keep"))
    with override_settings(STORAGES=storage_settings()), patch(
        "apps.common.management.commands.check_object_storage.default_storage", storage
    ):
        if read_fails:
            with patch.object(storage, "open", side_effect=OSError("unavailable")), \
                    pytest.raises(CommandError, match="probe failed"):
                call_command("check_object_storage", write=True, stdout=io.StringIO())
        else:
            call_command("check_object_storage", write=True, stdout=io.StringIO())
    assert storage.exists(original)
    assert list((tmp_path / "_healthchecks").iterdir()) == []
