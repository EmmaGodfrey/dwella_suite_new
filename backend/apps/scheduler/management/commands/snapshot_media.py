import os
import re
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.scheduler.management.commands.upload_backups import client
from apps.scheduler.media_backups import snapshot, verify_archive


class Command(BaseCommand):
    help = "Keep a verified local recovery snapshot of private S3/R2 media."

    def add_arguments(self, parser):
        parser.add_argument("--label", default="")

    def handle(self, *args, **options):
        if settings.STORAGES["default"]["BACKEND"] != "storages.backends.s3.S3Storage":
            self.stdout.write("R2 media snapshot skipped: local storage is active.")
            return
        label = options["label"] or timezone.now().strftime("%Y-%m-%d")
        if not re.fullmatch(r"[a-zA-Z0-9-]{1,80}", label):
            raise CommandError("Choose a label with letters, digits and hyphens only.")
        folder = Path(settings.BACKUP_DIR)
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = folder / f"media-r2-{label}.tar.gz"
        config = settings.STORAGES["default"]["OPTIONS"]
        target = {"bucket": config["bucket_name"], "endpoint": config["endpoint_url"],
                  "region": config["region_name"], "access_key": config["access_key"],
                  "secret_key": config["secret_key"]}
        try:
            if path.exists():
                count = len(verify_archive(path)["objects"])
            else:
                count = snapshot(client(target), target["bucket"], path)
        except Exception:
            raise CommandError("Media snapshot failed; the last complete archive is preserved.") \
                from None
        keep_days = int(os.getenv("BACKUP_KEEP_DAYS", "14"))
        if not 1 <= keep_days <= 365:
            raise CommandError("BACKUP_KEEP_DAYS must be between 1 and 365.")
        cutoff = (timezone.now() - timedelta(days=keep_days)).timestamp()
        for old in folder.glob("media-r2-*.tar.gz"):
            if old != path and old.stat().st_mtime < cutoff:
                old.unlink()
        self.stdout.write(f"Verified R2 recovery snapshot: {count} object(s).")
