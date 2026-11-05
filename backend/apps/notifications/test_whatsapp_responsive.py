"""Committed wakeups, isolated lanes, ordered recovery and conservative send ownership."""
import threading
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from redis.exceptions import ConnectionError as RedisConnectionError

from . import test_whatsapp as base
from .test_whatsapp import PHONE, incoming, linked, step
from .whatsapp.models import WhatsAppInbound, WhatsAppReply
from .whatsapp.responsive import LaneLease, cycle, run_lane
from .whatsapp.transport import dispatch_replies
from .whatsapp.wakeup import heartbeats, key, wait, wake
from .whatsapp.worker import process_inbox

pytestmark = pytest.mark.django_db(transaction=True)
config = base.config
house = base.house


@pytest.fixture(autouse=True)
def worker_settings(settings, monkeypatch):
    settings.WHATSAPP_WORKER_ENABLED = True
    settings.WHATSAPP_WORKER_REDIS_URL = ''
    monkeypatch.setattr('apps.notifications.whatsapp.wakeup._wake_retry_after', 0)


def test_wakeup_waits_for_commit_and_duplicate_does_not_wake():
    with patch('apps.notifications.whatsapp.wakeup.wake') as signal:
        with transaction.atomic():
            incoming()
            signal.assert_not_called()
        signal.assert_called_once_with()
        incoming(identity='wamid.1')
        assert signal.call_count == 1


def test_rollback_does_not_wake_or_keep_inbox():
    with patch('apps.notifications.whatsapp.wakeup.wake') as signal:
        with pytest.raises(RuntimeError), transaction.atomic():
            incoming()
            raise RuntimeError('rollback')
        signal.assert_not_called()
    assert not WhatsAppInbound.objects.exists()


def test_redis_outage_does_not_reject_committed_webhook(settings):
    settings.WHATSAPP_WORKER_REDIS_URL = 'redis://synthetic/1'
    with patch('apps.notifications.whatsapp.wakeup.client', side_effect=RedisConnectionError):
        incoming()
    assert WhatsAppInbound.objects.filter(status='queued').count() == 1


def test_wake_hint_is_constant_bounded_and_expires(settings):
    settings.WHATSAPP_WORKER_REDIS_URL = 'redis://synthetic/1'
    pipe = Mock()
    pipe.lpush.return_value = pipe.ltrim.return_value = pipe.expire.return_value = pipe
    redis = Mock()
    redis.pipeline.return_value.__enter__ = Mock(return_value=pipe)
    redis.pipeline.return_value.__exit__ = Mock(return_value=False)
    with patch('apps.notifications.whatsapp.wakeup.client', return_value=redis):
        wake()
    pipe.lpush.assert_called_once_with(key('fast'), '1')
    pipe.ltrim.assert_called_once_with(key('fast'), 0, 0)
    pipe.expire.assert_called_once_with(key('fast'), 60)


def test_redis_outage_does_not_multiply_timeout_for_batched_webhook(settings):
    settings.WHATSAPP_WORKER_REDIS_URL = 'redis://synthetic/1'
    with patch('apps.notifications.whatsapp.wakeup.client',
               side_effect=RedisConnectionError) as redis:
        for _ in range(100):
            wake()
    assert redis.call_count == 1


def test_disabled_worker_does_not_touch_redis_or_work(settings):
    settings.WHATSAPP_WORKER_ENABLED = False
    settings.WHATSAPP_WORKER_REDIS_URL = 'redis://synthetic/1'
    with patch('apps.notifications.whatsapp.wakeup.client') as redis:
        wake()
        assert cycle('fast') == 0
    redis.assert_not_called()


def test_failed_wake_wait_uses_bounded_recovery_delay(settings):
    settings.WHATSAPP_WORKER_REDIS_URL = 'redis://synthetic/1'
    stopping = Mock()
    with patch('apps.notifications.whatsapp.wakeup.client', side_effect=RedisConnectionError):
        wait('fast', stopping)
    assert 0 < stopping.wait.call_args.args[0] <= 2


def test_unavailable_heartbeat_store_does_not_block_database_recovery(settings):
    settings.WHATSAPP_WORKER_REDIS_URL = 'redis://synthetic/1'
    stopping = threading.Event()

    def process(lane):
        stopping.set()
        return 1

    with (patch('apps.notifications.whatsapp.responsive.LaneLease') as lease,
          patch('apps.notifications.whatsapp.responsive.heartbeat',
                side_effect=RedisConnectionError),
          patch('apps.notifications.whatsapp.responsive.cycle', side_effect=process) as work):
        lease.return_value.acquire.return_value = True
        run_lane('fast', stopping)
    work.assert_called_once_with('fast')
    lease.return_value.close.assert_called_once_with()
    with patch('apps.notifications.whatsapp.wakeup.client', side_effect=RedisConnectionError):
        assert heartbeats() == {'fast': None, 'files': None, 'notices': None}


def test_fast_cycle_recovers_without_redis_and_sends_before_next_turn(house):
    linked(house)
    incoming('Hi')
    incoming('balance')
    with patch('apps.notifications.whatsapp.transport.post_json',
               return_value={'messages': [{'id': 'wamid.immediate'}]}) as send:
        assert cycle('fast') == 2
        assert send.call_count == 1
        assert WhatsAppInbound.objects.filter(status='queued').count() == 1
        assert cycle('fast') == 2
        assert send.call_count == 2
    assert WhatsAppReply.objects.filter(status='sent').count() == 2


def test_older_retry_blocks_only_its_own_phone(house):
    linked(house)
    incoming('Hi')
    first = WhatsAppInbound.objects.get()
    first.available_at = timezone.now() + timedelta(minutes=1)
    first.save()
    incoming('balance')
    incoming('Hi', phone='+260971234568')
    assert process_inbox(ordered=True) == 1
    assert WhatsAppInbound.objects.filter(phone=PHONE, status='queued').count() == 2
    assert WhatsAppReply.objects.get().inbound.phone == '+260971234568'


def test_pending_reply_blocks_later_turn_without_advancing_revision(house):
    linked(house)
    step()
    incoming('balance')
    assert process_inbox(ordered=True) == 0
    assert WhatsAppInbound.objects.filter(status='queued').exists()


def test_oldest_queue_selection_query_count_is_bounded(house):
    linked(house)
    incoming()
    with CaptureQueriesContext(connection) as queries, patch(
        'apps.notifications.whatsapp.worker._process',
    ):
        process_inbox(ordered=True)
    first = len(queries)
    stamp = timezone.now()
    for index in range(50):
        WhatsAppInbound.objects.create(number_id='number-id', provider_id=f'bulk{index}',
                                       phone=f'+2609712{index:05d}', happened_at=stamp)
    with CaptureQueriesContext(connection) as queries, patch(
        'apps.notifications.whatsapp.worker._process',
    ):
        process_inbox(ordered=True)
    assert len(queries) == first == 1


def test_fast_reply_skips_file_work_and_files_lane_retains_guards(house):
    linked(house)
    reply = step()
    reply.view = {'text': 'Private file', 'document': {'kind': 'invoice'}}
    reply.save()
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        assert dispatch_replies(lane='fast') == 0
    send.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == 'queued'
    # A malformed scope still fails in the file lane before any provider I/O.
    reply.organization = None
    reply.save()
    with patch('apps.notifications.whatsapp.transport.post_request') as upload:
        assert dispatch_replies(lane='files') == 0
    upload.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == 'cancelled'


@pytest.mark.parametrize('status', ['sent', 'read', 'review', 'sending'])
def test_fast_worker_never_replays_claimed_or_uncertain_reply(house, status):
    linked(house)
    reply = step()
    reply.status, reply.claimed_at = status, timezone.now()
    reply.save()
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        dispatch_replies(lane='fast')
    send.assert_not_called()


@pytest.mark.parametrize('change', ['stop', 'membership', 'binding'])
def test_new_dispatch_lane_preserves_current_authority(house, change):
    from apps.organizations.models import OrganizationMembership

    from .models import PhoneMessagingConsent
    from .whatsapp.access import revoke

    linked(house)
    reply = step()
    if change == 'stop':
        PhoneMessagingConsent.objects.update(revoked_at=timezone.now())
    elif change == 'membership':
        OrganizationMembership.objects.filter(user=house['tenant']).update(is_active=False)
    else:
        revoke(phone=PHONE)
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        dispatch_replies(lane='fast')
    send.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == 'cancelled'


def test_minute_scheduler_only_cleans_when_dedicated_worker_enabled():
    with (patch('apps.notifications.management.commands.run_whatsapp.process_inbox') as process,
          patch('apps.notifications.management.commands.run_whatsapp.fetch_media') as fetch,
          patch('apps.notifications.management.commands.run_whatsapp.dispatch_replies') as send,
          patch('apps.notifications.management.commands.run_whatsapp.cleanup') as cleanup):
        call_command('run_whatsapp')
    process.assert_not_called()
    fetch.assert_not_called()
    send.assert_not_called()
    cleanup.assert_called_once_with()


@pytest.mark.skipif(connection.vendor != 'postgresql', reason='PostgreSQL session lease')
def test_session_lease_excludes_second_consumer_and_recovers_after_release():
    first, second = LaneLease('fast'), LaneLease('fast')
    other = LaneLease('files')
    try:
        assert first.acquire() and first.acquire()  # No reentrant lock stacking.
        assert not second.acquire()
        assert other.acquire()
        first.close()
        assert second.acquire()
    finally:
        first.close()
        second.close()
        other.close()


def test_file_lane_cannot_hold_up_fast_lane(house):
    linked(house)
    incoming('Hi')
    entered, release = threading.Event(), threading.Event()

    def slow(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return 0

    with patch('apps.notifications.whatsapp.responsive.fetch_media', side_effect=slow), patch(
        'apps.notifications.whatsapp.responsive.dispatch_replies', return_value=1,
    ):
        thread = threading.Thread(target=lambda: cycle('files'))
        thread.start()
        try:
            assert entered.wait(2)
            assert cycle('fast') == 2
            assert thread.is_alive()
        finally:
            release.set()
            thread.join(5)
