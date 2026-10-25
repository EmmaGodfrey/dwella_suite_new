from django.core.management.base import BaseCommand

from apps.documents.outbox import deliver_pending


class Command(BaseCommand):
    help = "Deliver due signing outbox entries without holding signing locks."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        count = deliver_pending(limit=max(1, min(options["limit"], 100)))
        self.stdout.write(f"Signing outbox: {count} delivered.")
