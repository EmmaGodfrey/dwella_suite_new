import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from django.core.management import call_command
from django.core.management.base import CommandError


class FakeS3:
    exceptions = SimpleNamespace(ClientError=ClientError)

    def __init__(self, fail_upload=False):
        self.objects, self.fail_upload, self.uploads = {}, fail_upload, []

    def head_object(self, Bucket, Key):  # noqa: N803
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {"ContentLength": len(self.objects[Key])}

    def upload_file(self, filename, bucket, key):
        if self.fail_upload:
            raise ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "secret-key-context"}}, "PutObject"
            )
        self.uploads.append(key)
        with open(filename, "rb") as stream:
            self.objects[key] = stream.read()


@pytest.fixture
def backups(tmp_path, settings, monkeypatch):
    settings.BACKUP_DIR = str(tmp_path)
    for name in ["BUCKET", "ACCESS_KEY", "SECRET_KEY", "ENDPOINT_URL"]:
        monkeypatch.delenv(f"BACKUP_S3_{name}", raising=False)
    monkeypatch.setenv("STORAGE_S3_BUCKET", "dwella-test-media")
    monkeypatch.setenv("STORAGE_S3_ACCESS_KEY", "key")
    monkeypatch.setenv("STORAGE_S3_SECRET_KEY", "secret")
    monkeypatch.setenv("BACKUP_S3_PREFIX", "_backups/test")
    (tmp_path / "db-2026-11-20.dump").write_bytes(b"dump")
    (tmp_path / "media-2026-11-20.tar.gz").write_bytes(b"media")
    (tmp_path / "pre-deploy-20261120T060000Z.dump").write_bytes(b"pre")
    (tmp_path / "db-2026-11-21.dump.tmp").write_bytes(b"partial")
    (tmp_path / "notes.txt").write_bytes(b"ignore")
    return tmp_path


def run(fake):
    out = io.StringIO()
    with patch("apps.scheduler.management.commands.upload_backups.client", return_value=fake):
        call_command("upload_backups", stdout=out)
    return out.getvalue()


def test_new_backups_upload_once_and_partial_files_are_skipped(backups):
    fake = FakeS3()
    assert "3 uploaded" in run(fake)
    assert sorted(fake.objects) == [
        "_backups/test/db-2026-11-20.dump",
        "_backups/test/media-2026-11-20.tar.gz",
        "_backups/test/pre-deploy-20261120T060000Z.dump",
    ]
    assert "0 uploaded" in run(fake)
    (backups / "db-2026-11-21.dump").write_bytes(b"next")
    assert "1 uploaded" in run(fake)


def test_incomplete_remote_copy_is_replaced(backups):
    fake = FakeS3()
    fake.objects["_backups/test/db-2026-11-20.dump"] = b"du"
    run(fake)
    assert fake.objects["_backups/test/db-2026-11-20.dump"] == b"dump"


def test_dedicated_backup_credentials_take_priority(backups, monkeypatch):
    from apps.scheduler.management.commands.upload_backups import backup_target

    monkeypatch.setenv("BACKUP_S3_BUCKET", "dwella-backups")
    monkeypatch.setenv("BACKUP_S3_ACCESS_KEY", "backup-key")
    monkeypatch.setenv("BACKUP_S3_SECRET_KEY", "backup-secret")
    target = backup_target()
    assert (target["bucket"], target["access_key"]) == ("dwella-backups", "backup-key")
    assert target["prefix"] == "_backups/test/"


def test_failures_are_reported_without_sdk_details(backups):
    with pytest.raises(CommandError) as error:
        run(FakeS3(fail_upload=True))
    assert "failed" in str(error.value)
    assert error.value.__cause__ is None and error.value.__suppress_context__
    assert "secret-key-context" not in str(error.value)


def test_missing_configuration_fails_loudly(backups, monkeypatch):
    monkeypatch.delenv("STORAGE_S3_BUCKET")
    with pytest.raises(CommandError, match="not configured"):
        run(FakeS3())
