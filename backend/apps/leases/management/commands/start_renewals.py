from django.core.management.base import BaseCommand

from apps.leases.services import start_due_renewals


class Command(BaseCommand):
    help = "Start signed lease renewals whose start date has arrived."

    def handle(self, *args, **options):
        started = start_due_renewals()
        self.stdout.write(f"Started {len(started)} renewal(s).")
