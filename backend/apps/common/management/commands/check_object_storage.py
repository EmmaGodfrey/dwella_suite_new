import secrets

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Check object-storage configuration; --write tests an isolated upload/read/delete."

    def add_arguments(self, parser):
        parser.add_argument("--write", action="store_true")

    def handle(self, *args, **options):
        if settings.STORAGES["default"]["BACKEND"] != "storages.backends.s3.S3Storage":
            raise CommandError("Object storage is disabled; uploads still use local storage.")
        self.stdout.write("Private S3 storage configured; signed URLs enabled.")
        if not options["write"]:
            self.stdout.write("No remote requests made. Use --write to test connectivity.")
            return
        key = f"_healthchecks/{secrets.token_hex(24)}.txt"
        payload = secrets.token_bytes(32)
        saved = None
        try:
            saved = default_storage.save(key, ContentFile(payload))
            with default_storage.open(saved, "rb") as stream:
                if stream.read() != payload:
                    raise CommandError("Object storage returned different bytes.")
            self.stdout.write("Upload and read verified.")
        except Exception as error:
            # SDK errors can contain signed URLs or credential context.
            raise CommandError("Object storage probe failed; check endpoint and bucket access.") \
                from error
        finally:
            if saved is not None:
                try:
                    default_storage.delete(saved)
                except Exception as error:
                    raise CommandError("Probe cleanup failed; remove the _healthchecks object.") \
                        from error
        self.stdout.write(self.style.SUCCESS("Object storage write/read/delete passed."))
