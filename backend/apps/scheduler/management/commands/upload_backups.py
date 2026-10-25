import hashlib
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

PATTERNS = ("db-*.dump", "media-*.tar.gz", "pre-deploy-*.dump")


def backup_target():
    """Dedicated BACKUP_S3_* credentials, else the environment's media bucket."""

    def value(name):
        return (
            os.getenv(f"BACKUP_S3_{name}", "").strip()
            or os.getenv(f"STORAGE_S3_{name}", "").strip()
        )

    target = {
        "bucket": value("BUCKET"),
        "endpoint": value("ENDPOINT_URL") or None,
        "region": value("REGION") or "auto",
        "access_key": value("ACCESS_KEY"),
        "secret_key": value("SECRET_KEY"),
        "prefix": os.getenv("BACKUP_S3_PREFIX", "_backups/").strip().strip("/") + "/",
    }
    if not (target["bucket"] and target["access_key"] and target["secret_key"]):
        raise CommandError(
            "Off-server backups are not configured: set BACKUP_S3_* or STORAGE_S3_* credentials."
        )
    return target


def client(target):
    import boto3
    from botocore.config import Config

    return boto3.client(
        "s3",
        endpoint_url=target["endpoint"],
        region_name=target["region"],
        aws_access_key_id=target["access_key"],
        aws_secret_access_key=target["secret_key"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


class Command(BaseCommand):
    help = "Copy local database/media backups that are not yet off-server to the backup bucket."

    def handle(self, *args, **options):
        folder = Path(settings.BACKUP_DIR)
        if not folder.is_dir():
            raise CommandError(f"Backup folder {folder} does not exist.")
        target = backup_target()
        s3 = client(target)
        files = sorted({path for pattern in PATTERNS for path in folder.glob(pattern)})
        uploaded = 0
        for path in files:
            key = target["prefix"] + path.name
            size = path.stat().st_size
            with path.open("rb") as source:
                sha256 = hashlib.file_digest(source, "sha256").hexdigest()
            try:
                try:
                    remote = s3.head_object(Bucket=target["bucket"], Key=key)
                    if (remote["ContentLength"] == size
                            and remote.get("Metadata", {}).get("sha256") == sha256):
                        continue
                except s3.exceptions.ClientError as error:
                    if error.response.get("Error", {}).get("Code") not in {"404", "NoSuchKey"}:
                        raise
                s3.upload_file(str(path), target["bucket"], key,
                               ExtraArgs={"Metadata": {"sha256": sha256}})
                if s3.head_object(Bucket=target["bucket"], Key=key)["ContentLength"] != size:
                    raise CommandError(f"{path.name} did not upload completely.")
                body = s3.get_object(Bucket=target["bucket"], Key=key)["Body"]
                try:
                    remote_hash = hashlib.sha256()
                    for block in iter(lambda stream=body: stream.read(1024 * 1024), b""):
                        remote_hash.update(block)
                    if remote_hash.hexdigest() != sha256:
                        raise CommandError("Offsite backup checksum verification failed.")
                finally:
                    body.close()
            except CommandError:
                raise
            except Exception:
                # SDK errors can carry endpoint and credential context; keep them out of logs.
                raise CommandError(
                    f"Uploading {path.name} failed; check the backup bucket and credentials."
                ) from None
            uploaded += 1
        self.stdout.write(f"Off-server backups: {uploaded} uploaded, {len(files)} local files.")
