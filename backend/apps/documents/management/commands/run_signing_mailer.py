import signal
import time

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from apps.documents.outbox import deliver_pending


class Command(BaseCommand):
    help = "Process committed signing emails independently of backup and billing jobs."

    def handle(self, *args, **options):
        stopping = []
        signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
        self.stdout.write("Signing outbox worker started.")
        while not stopping:
            close_old_connections()
            cache.set("signing-mailer:heartbeat", timezone.now().isoformat(), timeout=120)
            count = deliver_pending()
            if count:
                self.stdout.write(f"Signing outbox: {count} delivered.")
            for _ in range(5):
                if stopping:
                    return
                time.sleep(1)
