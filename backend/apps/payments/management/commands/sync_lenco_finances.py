from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.payments.balances import sync_balance


class Command(BaseCommand):
    help = "Import Lenco credits/debits and compare balances without moving money."

    def handle(self, *args, **options):
        try:
            UUID(settings.LENCO_DEBIT_ACCOUNT_ID)
        except (ValueError, TypeError):
            raise CommandError("Configure LENCO_DEBIT_ACCOUNT_ID first.") from None
        snapshot = sync_balance()
        self.stdout.write(
            f"Lenco reconciliation: {snapshot.status}; imported records: "
            f"{snapshot.transaction_count}. No payment was initiated."
        )
