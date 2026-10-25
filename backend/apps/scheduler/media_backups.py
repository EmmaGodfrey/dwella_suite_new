"""Verified, portable snapshots of private object storage, without recursive backups."""

import hashlib
import io
import json
import os
import tarfile
from pathlib import Path, PurePosixPath

from django.core.management.base import CommandError

MANIFEST = "manifest.json"
EXCLUDED = ("_backups/", "_healthchecks/")


def safe_key(key):
    parts = PurePosixPath(key).parts
    if (not key or key.startswith("/") or "\\" in key or ".." in parts
            or any(ord(char) < 32 for char in key)
            or str(PurePosixPath(key)) != key):
        raise CommandError("Snapshot contains an unsafe object name.")
    return key


class DigestReader:
    def __init__(self, source):
        self.source = source
        self.digest = hashlib.sha256()

    def read(self, size=-1):
        data = self.source.read(size)
        self.digest.update(data)
        return data


def snapshot(s3, bucket, destination):
    destination = Path(destination)
    temporary = destination.with_name(destination.name + ".tmp")
    manifest = {"version": 1, "source_bucket": bucket, "objects": []}
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with (
            os.fdopen(descriptor, "wb") as output,
            tarfile.open(fileobj=output, mode="w:gz") as archive,
        ):
            for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket):
                for entry in page.get("Contents", []):
                    key = entry["Key"]
                    if key.startswith(EXCLUDED) or key.endswith("/"):
                        continue
                    safe_key(key)
                    response = s3.get_object(Bucket=bucket, Key=key)
                    source = response["Body"]
                    try:
                        size = int(response["ContentLength"])
                        info = tarfile.TarInfo("objects/" + key)
                        info.size, info.mode = size, 0o600
                        reader = DigestReader(source)
                        archive.addfile(info, reader)
                        manifest["objects"].append({
                            "key": key, "size": size, "sha256": reader.digest.hexdigest(),
                        })
                    finally:
                        source.close()
            raw = json.dumps(manifest, sort_keys=True).encode()
            info = tarfile.TarInfo(MANIFEST)
            info.size, info.mode = len(raw), 0o600
            archive.addfile(info, io.BytesIO(raw))
        verify_archive(temporary)
        os.replace(temporary, destination)
        return len(manifest["objects"])
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def verify_archive(path):
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)) or any(not m.isfile() for m in members):
                raise CommandError("Snapshot contains duplicate or non-file entries.")
            manifest_info = archive.getmember(MANIFEST)
            if manifest_info.size > 8 * 1024 * 1024:
                raise CommandError("Snapshot manifest is too large.")
            manifest = json.load(archive.extractfile(manifest_info))
            if manifest.get("version") != 1:
                raise CommandError("Unsupported snapshot version.")
            expected = {MANIFEST}
            for item in manifest["objects"]:
                key = safe_key(item["key"])
                name = "objects/" + key
                if name in expected or key.startswith(EXCLUDED):
                    raise CommandError("Snapshot contains duplicate or excluded objects.")
                expected.add(name)
                info = archive.getmember(name)
                if info.size != item["size"]:
                    raise CommandError("Snapshot size check failed.")
                digest = hashlib.sha256()
                with archive.extractfile(info) as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(block)
                if digest.hexdigest() != item["sha256"]:
                    raise CommandError("Snapshot checksum check failed.")
            if set(names) != expected:
                raise CommandError("Snapshot contains unlisted objects.")
            return manifest
    except CommandError:
        raise
    except Exception:
        raise CommandError("Invalid or incomplete media snapshot.") from None


def restore_archive(path, destination):
    manifest = verify_archive(path)
    destination = Path(destination)
    if destination.is_symlink() or (destination.exists() and any(destination.iterdir())):
        raise CommandError("Restore destination must be an empty directory, without symlinks.")
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(path, "r:gz") as archive:
        for item in manifest["objects"]:
            target = destination / item["key"]
            if not target.resolve().is_relative_to(root):
                raise CommandError("Restore path is outside the destination.")
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with archive.extractfile("objects/" + item["key"]) as source:
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, "wb") as output:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        output.write(block)
    return len(manifest["objects"])
