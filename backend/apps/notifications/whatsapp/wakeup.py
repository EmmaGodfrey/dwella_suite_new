"""Bounded, disposable wake hints. Committed database rows remain the work queue."""
import logging
import time
from functools import lru_cache

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from redis import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)
LANES = ('fast', 'files', 'notices')
_last_warning = 0.0
_wake_retry_after = 0.0


@lru_cache(maxsize=4)
def client(url, blocking=False):
    return Redis.from_url(url, socket_connect_timeout=0.2, socket_timeout=3 if blocking else 0.2,
                          retry_on_timeout=False)


def key(lane):
    if lane not in LANES:
        raise ValueError('Unknown WhatsApp worker lane.')
    return f'dwella:whatsapp:wake:{settings.APP_ENVIRONMENT}:{lane}'


def unavailable():
    global _last_warning
    now = time.monotonic()
    if now - _last_warning >= 60:
        _last_warning = now
        logger.warning('WhatsApp wake service unavailable; using database recovery.')


def wake(lane='fast'):
    global _wake_retry_after
    name = key(lane)
    if not settings.WHATSAPP_WORKER_ENABLED or not settings.WHATSAPP_WORKER_REDIS_URL:
        return
    # One webhook may commit many events. A failed Redis connection must not add
    # its timeout to every callback in that batch; durable recovery covers the gap.
    if time.monotonic() < _wake_retry_after:
        return
    try:
        with client(settings.WHATSAPP_WORKER_REDIS_URL).pipeline(transaction=True) as pipe:
            pipe.lpush(name, '1').ltrim(name, 0, 0).expire(name, 60).execute()
    except (RedisError, ValueError):
        # A notification failure must never make Meta retry a committed domain action.
        unavailable()
        _wake_retry_after = time.monotonic() + 2


def wait(lane, stopping):
    name = key(lane)
    if settings.WHATSAPP_WORKER_REDIS_URL:
        started = time.monotonic()
        try:
            client(settings.WHATSAPP_WORKER_REDIS_URL, True).blpop(name, timeout=2)
            return
        except (RedisError, ValueError):
            unavailable()
            # Redis failure is rate bounded, rather than spinning on reconnect errors.
            stopping.wait(max(0, 2 - (time.monotonic() - started)))
    else:
        stopping.wait(2)


def heartbeat(lane):
    name = key(lane).replace(':wake:', ':heartbeat:')
    stamp = timezone.now().isoformat()
    if settings.WHATSAPP_WORKER_REDIS_URL:
        # Use the bounded client: an unreachable cache must not stall queue recovery.
        client(settings.WHATSAPP_WORKER_REDIS_URL).set(name, stamp, ex=60)
    else:
        cache.set(name, stamp, timeout=60)


def heartbeats():
    names = [key(lane).replace(':wake:', ':heartbeat:') for lane in LANES]
    try:
        if settings.WHATSAPP_WORKER_REDIS_URL:
            values = client(settings.WHATSAPP_WORKER_REDIS_URL).mget(names)
            return {lane: value.decode() if value else None
                    for lane, value in zip(LANES, values, strict=True)}
        return {lane: cache.get(name) for lane, name in zip(LANES, names, strict=True)}
    except (RedisError, ValueError):
        return dict.fromkeys(LANES)
