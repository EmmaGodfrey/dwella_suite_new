"""Independent bounded lanes, session leases and periodic database recovery."""
import logging
import time

from django.conf import settings
from django.db import close_old_connections, connections

from .media import fetch_media
from .notices import dispatch_proof_notices
from .transport import dispatch_replies
from .wakeup import LANES, heartbeat, wait, wake
from .worker import process_inbox

logger = logging.getLogger(__name__)


class LaneLease:
    """Separate PostgreSQL session: Redis outages cannot start competing consumers."""

    def __init__(self, lane):
        self.lock_id = 682400 + LANES.index(lane)
        self.connection = None

    def acquire(self):
        if self.connection is not None:
            with self.connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            return True
        conn = connections['default'].copy(alias=f'wa_lease_{self.lock_id}')
        try:
            conn.ensure_connection()
            if conn.vendor == 'postgresql':
                with conn.cursor() as cursor:
                    cursor.execute('SELECT pg_try_advisory_lock(%s)', [self.lock_id])
                    if not cursor.fetchone()[0]:
                        conn.close()
                        return False
            # SQLite development has a single command process; production uses PostgreSQL.
            self.connection = conn
            return True
        except Exception:
            conn.close()
            raise

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None


def cycle(lane):
    if not settings.WHATSAPP_WORKER_ENABLED or not settings.WHATSAPP_SELF_SERVICE_ENABLED:
        return 0
    if lane == 'fast':
        # Dispatch each turn before advancing another conversation revision.
        processed = process_inbox(limit=1, seconds=2, ordered=True)
        accepted = dispatch_replies(limit=1, seconds=2, lane='fast')
        if processed:
            wake('files')
            wake('notices')
        return processed + accepted
    if lane == 'files':
        completed = fetch_media(limit=1, seconds=2) + dispatch_replies(
            limit=1, seconds=2, lane='files',
        )
        if completed:
            wake('fast')
        return completed
    if lane == 'notices':
        return dispatch_proof_notices(limit=1, seconds=2)
    raise ValueError('Unknown worker lane.')


def run_lane(lane, stopping):
    lease = LaneLease(lane)
    heartbeat_at = 0.0
    warned_at = 0.0
    try:
        while not stopping.is_set():
            if not settings.WHATSAPP_WORKER_ENABLED or not settings.WHATSAPP_SELF_SERVICE_ENABLED:
                stopping.wait(2)
                continue
            busy = False
            try:
                if not lease.acquire():
                    stopping.wait(2)
                    continue
                close_old_connections()
                if time.monotonic() - heartbeat_at >= 15:
                    heartbeat_at = time.monotonic()
                    try:
                        heartbeat(lane)
                    except Exception:
                        # Cache availability is never the authority for queue ownership.
                        pass
                busy = cycle(lane) > 0
            except Exception as error:
                lease.close()
                if time.monotonic() - warned_at >= 60:
                    warned_at = time.monotonic()
                    logger.warning('WhatsApp worker lane=%s error=%s', lane, type(error).__name__)
                stopping.wait(2)
            finally:
                close_old_connections()
            if not busy:
                wait(lane, stopping)
    finally:
        lease.close()
        connections.close_all()
