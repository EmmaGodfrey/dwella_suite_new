import signal
import time

from django.core.management.base import BaseCommand

from apps.scheduler.services import enabled_jobs, run_due_jobs


class Command(BaseCommand):
    help = "Run due recurring jobs every minute (or once with --once). Safe to restart."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run due jobs once and exit.")
        parser.add_argument("--interval", type=int, default=60, help="Seconds between checks.")

    def handle(self, *args, once=False, interval=60, **options):
        stopping = []
        signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
        self.stdout.write(f"Scheduler enabled jobs: {', '.join(enabled_jobs()) or 'none'}")
        while not stopping:
            for run in run_due_jobs():
                self.stdout.write(f"{run.job}: {run.status}")
            if once:
                return
            for _ in range(interval):
                if stopping:
                    break
                time.sleep(1)
