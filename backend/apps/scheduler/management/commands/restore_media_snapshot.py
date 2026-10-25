from django.core.management.base import BaseCommand

from apps.scheduler.media_backups import restore_archive


class Command(BaseCommand):
    help = "Verify and restore a media snapshot into an empty local directory. Never writes R2."

    def add_arguments(self, parser):
        parser.add_argument("archive")
        parser.add_argument("destination")

    def handle(self, *args, **options):
        count = restore_archive(options["archive"], options["destination"])
        self.stdout.write(f"Restored and verified {count} media object(s).")
