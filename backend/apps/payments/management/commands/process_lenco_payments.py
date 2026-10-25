from django.core.management.base import BaseCommand

from apps.payments.worker import run_cycle


class Command(BaseCommand):
    help = "Reconcile queued Lenco collections and process approved landlord payouts."

    def handle(self, *args, **options):
        count = run_cycle()
        self.stdout.write(f"Processed {count} payment reconciliation items.")
