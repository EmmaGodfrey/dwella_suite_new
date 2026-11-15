"""Wake the payments worker the moment there is something to check.

A webhook or a tenant's "check status" only brings a row's next check
forward; this nudge makes the idle worker look at it straight away instead
of after its idle pause. The nudge carries nothing: the worker still picks
due rows from the database and verifies them with Lenco, so a lost or
repeated nudge changes timing, never outcomes.
"""

import time

from django.core.cache import cache
from django.db import transaction

WAKE_KEY = "payments-worker:wake"
POLL_SECONDS = 0.25


def wake():
    """Nudge the worker once the current transaction commits."""
    transaction.on_commit(lambda: cache.set(WAKE_KEY, 1, timeout=60))


def wait(seconds, stopping):
    """Idle up to ``seconds``; return True early when nudged or stopping."""
    deadline = time.monotonic() + seconds
    while not stopping and time.monotonic() < deadline:
        if cache.get(WAKE_KEY):
            cache.delete(WAKE_KEY)
            return True
        time.sleep(POLL_SECONDS)
    return False
