import logging
import signal
import time
from uuid import UUID, uuid4

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from apps.payments.balances import sync_balance
from apps.payments.worker import run_cycle

logger = logging.getLogger(__name__)
HEARTBEAT_KEY = "payments-worker:heartbeat"
LOCK_KEY = "payments-worker:lock"
BALANCE_EVERY = 5 * 60
IDLE_SECONDS = 5


def balance_configured():
    try:
        UUID(settings.LENCO_DEBIT_ACCOUNT_ID)
    except (ValueError, TypeError):
        return False
    return True


class Command(BaseCommand):
    help = (
        "Check due Lenco collections and payouts, and reconcile the balance every five "
        "minutes, independently of the scheduler. Writes no per-run records."
    )

    def handle(self, *args, **options):
        stopping = []
        signal.signal(signal.SIGTERM, lambda *_: stopping.append(True))
        self.stdout.write("Payments worker started.")
        last_balance = 0.0
        token = uuid4().hex
        while not stopping:
            close_old_connections()
            # One worker at a time; a crashed one's lock expires on its own.
            if cache.add(LOCK_KEY, token, timeout=120) or cache.get(LOCK_KEY) == token:
                cache.touch(LOCK_KEY, 120)
            else:
                time.sleep(IDLE_SECONDS)
                continue
            cache.set(HEARTBEAT_KEY, timezone.now().isoformat(), timeout=120)
            busy = False
            try:
                busy = run_cycle() > 0
                if balance_configured() and time.monotonic() - last_balance >= BALANCE_EVERY:
                    last_balance = time.monotonic()
                    snapshot = sync_balance()
                    if snapshot.status not in {"matched", "baseline"}:
                        logger.warning(
                            "Lenco balance %s: %s", snapshot.status, snapshot.issue or "-"
                        )
            except Exception:  # Keep the worker alive; the next pass retries.
                logger.exception("Payments worker pass failed")
            if busy:
                continue
            for _ in range(IDLE_SECONDS):
                if stopping:
                    break
                time.sleep(1)
        if cache.get(LOCK_KEY) == token:
            cache.delete(LOCK_KEY)
