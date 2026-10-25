import hashlib
import io
import json
import tarfile

import pytest
from django.core.management.base import CommandError

from .media_backups import restore_archive, safe_key, snapshot, verify_archive


class FakeMedia:
    def __init__(self, objects):
        self.objects = objects

    def get_paginator(self, operation):
        assert operation == "list_objects_v2"
        return self

    def paginate(self, **kwargs):
        yield {"Contents": [{"Key": key} for key in self.objects]}

    def get_object(self, Bucket, Key):  # noqa: N803
        raw = self.objects[Key]
        return {"Body": io.BytesIO(raw), "ContentLength": len(raw)}


def test_media_round_trip_is_independent_and_preserves_keys_and_bytes(tmp_path):
    path = tmp_path / "media.tar.gz"
    data = {"profiles/a.png": b"private", "properties/picture.png": b"image"}
    source = FakeMedia({**data, "_backups/archive.tar.gz": b"skip", "_healthchecks/check": b"skip"})
    assert snapshot(source, "private-bucket", path) == 2
    source.objects.clear()  # Recovery must not depend on the live bucket.
    restored = tmp_path / "restored"
    assert restore_archive(path, restored) == 2
    for key, raw in data.items():
        assert (restored / key).read_bytes() == raw
    assert not (restored / "_backups").exists()


@pytest.mark.parametrize("key", ["../escape", "/absolute", "a/../escape", "a\\escape", "a//b",
                                  "a/./b", "a\nname"])
def test_unsafe_object_names_rejected(key):
    with pytest.raises(CommandError, match="unsafe"):
        safe_key(key)


def malicious_archive(path, key="../escape", raw=b"data", digest=None, extra=None):
    manifest = {"version": 1, "objects": [{"key": key, "size": len(raw),
                "sha256": digest or hashlib.sha256(raw).hexdigest()}]}
    with tarfile.open(path, "w:gz") as archive:
        entries = [("objects/" + key, raw), ("manifest.json", json.dumps(manifest).encode())]
        for name, value in entries:
            info = tarfile.TarInfo(name)
            info.size = len(value)
            archive.addfile(info, io.BytesIO(value))
        if extra:
            archive.addfile(extra)


def test_restore_rejects_traversal_before_creating_destination(tmp_path):
    path, destination = tmp_path / "bad.tar.gz", tmp_path / "restore"
    malicious_archive(path)
    with pytest.raises(CommandError):
        restore_archive(path, destination)
    assert not destination.exists()
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize("corruption", ["digest", "symlink", "duplicate", "unlisted"])
def test_corrupt_or_special_archives_are_refused(tmp_path, corruption):
    path = tmp_path / "bad.tar.gz"
    extra = None
    if corruption == "symlink":
        extra = tarfile.TarInfo("link")
        extra.type, extra.linkname = tarfile.SYMTYPE, "/etc/passwd"
    elif corruption == "duplicate":
        extra = tarfile.TarInfo("objects/photo.png")
    elif corruption == "unlisted":
        extra = tarfile.TarInfo("unlisted")
    malicious_archive(path, key="photo.png", digest="0" * 64 if corruption == "digest" else None,
                      extra=extra)
    with pytest.raises(CommandError):
        verify_archive(path)


def test_restore_never_overwrites_existing_data(tmp_path):
    path, destination = tmp_path / "media.tar.gz", tmp_path / "restore"
    snapshot(FakeMedia({"photo.png": b"snapshot"}), "bucket", path)
    destination.mkdir()
    (destination / "photo.png").write_bytes(b"keep")
    with pytest.raises(CommandError, match="empty"):
        restore_archive(path, destination)
    assert (destination / "photo.png").read_bytes() == b"keep"


def test_failed_snapshot_keeps_last_complete_backup(tmp_path):
    path = tmp_path / "media.tar.gz"
    snapshot(FakeMedia({"photo.png": b"first"}), "bucket", path)
    before = path.read_bytes()

    class Broken(FakeMedia):
        def get_object(self, **kwargs):
            raise OSError("private provider context")

    with pytest.raises(OSError):
        snapshot(Broken({"photo.png": b"next"}), "bucket", path)
    assert path.read_bytes() == before
    assert not path.with_name(path.name + ".tmp").exists()
