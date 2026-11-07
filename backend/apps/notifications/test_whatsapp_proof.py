"""The guided WhatsApp payment-proof flow, end to end through signed webhooks."""
import hashlib
from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

import pytest
from django.utils import timezone
from PIL import Image

from apps.common.provider_http import ProviderRejected

from . import test_whatsapp as base
from .models import PhoneMessagingConsent
from .test_whatsapp import PHONE, callback, choose, incoming, linked, step, workspace
from .whatsapp.media import cleanup_media, fetch_media, keep
from .whatsapp.models import (
    WhatsAppBinding,
    WhatsAppConversation,
    WhatsAppInbound,
    WhatsAppMedia,
    WhatsAppReply,
)
from .whatsapp.worker import process_inbox

pytestmark = pytest.mark.django_db
config = base.config
house = base.house


def png():
    raw = BytesIO()
    Image.new('RGB', (40, 40), 'white').save(raw, format='PNG')
    return raw.getvalue()


def attachment(identity='wamid.image', media='meta-media-1', kind='image'):
    row = {'id': identity, 'from': PHONE[1:], 'type': kind,
           'timestamp': str(int(timezone.now().timestamp())),
           kind: {'id': media, 'mime_type': 'image/png'}}
    assert callback([row]).status_code == 200


def drafted(binding):
    row = keep(binding, 'meta-media-1')
    conversation, _ = WhatsAppConversation.objects.get_or_create(
        binding=binding, defaults={'generation': binding.generation},
    )
    conversation.draft = {'intent': 'payment_proof', 'files': [row.pk]}
    conversation.save()
    return row


META = {'url': 'https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1',
        'mime_type': 'image/png', 'file_size': 100}


def connected():
    return WhatsAppBinding.objects.filter(phone=PHONE, revoked_at__isnull=True).exists()


def test_cancel_exits_the_step_and_keeps_the_connection(house):
    menu = workspace(house)
    homes = step(token=choose(menu, 'Report a repair'))
    step(token=homes.view['options'][0]['id'])

    reply = step('cancel')

    assert connected()
    assert reply.view['text'].endswith('Cancelled. Nothing was sent.')
    assert PhoneMessagingConsent.objects.get(channel='whatsapp', phone=PHONE).revoked_at is None


@pytest.mark.parametrize('word', ['STOP', 'unsubscribe'])
def test_stop_and_unsubscribe_still_opt_out(house, word):
    workspace(house)
    incoming(word)
    process_inbox()
    assert not connected()
    assert PhoneMessagingConsent.objects.get(channel='whatsapp', phone=PHONE).revoked_at
    assert WhatsAppInbound.objects.latest('pk').reason == 'control_message'


def test_manager_typing_a_tenant_word_is_not_disconnected(house):
    workspace(house, 'manager')
    reply = step('pop')
    assert connected()
    assert 'not available for this account' in reply.view['text']
    assert WhatsAppReply.objects.filter(pk=reply.pk).exists()


def test_inbound_file_keeps_only_a_reference(house):
    workspace(house)
    attachment()
    assert WhatsAppInbound.objects.get(provider_id='wamid.image').payload == {
        'type': 'attachment', 'media_id': 'meta-media-1',
    }


def test_files_outside_a_draft_are_never_downloaded(house):
    binding = linked(house)
    row = keep(binding, 'meta-media-1')
    with patch('apps.notifications.whatsapp.media.get_json') as lookup:
        assert fetch_media() == 0
    lookup.assert_not_called()
    assert not WhatsAppMedia.objects.filter(pk=row.pk).exists()


def test_valid_file_is_cleaned_and_kept_for_the_draft(house):
    row = drafted(linked(house))
    raw = png()
    meta = {**META, 'sha256': hashlib.sha256(raw).hexdigest()}
    with patch('apps.notifications.whatsapp.media.get_json', return_value=meta), patch(
        'apps.notifications.whatsapp.media.get_bytes', return_value=raw,
    ):
        assert fetch_media() == 1
    row.refresh_from_db()
    assert (row.status, row.content_type) == ('ready', 'image/jpeg')
    assert bytes(row.content).startswith(b'\xff\xd8')


@pytest.mark.parametrize('meta,content', [
    ({**META, 'mime_type': 'application/zip'}, b'x'),
    ({**META, 'file_size': 9 * 1024 ** 2}, b'x'),
    (META, b'this is not an image'),
])
def test_unusable_files_are_rejected(house, meta, content):
    row = drafted(linked(house))
    with patch('apps.notifications.whatsapp.media.get_json', return_value=meta), patch(
        'apps.notifications.whatsapp.media.get_bytes', return_value=content,
    ):
        assert fetch_media() == 0
    row.refresh_from_db()
    assert row.status == 'rejected' and row.content is None


def test_token_is_not_sent_to_an_unexpected_host(house):
    row = drafted(linked(house))
    meta = {**META, 'url': 'https://example.com/file'}
    with patch('apps.notifications.whatsapp.media.get_json', return_value=meta), patch(
        'apps.notifications.whatsapp.media.get_bytes',
    ) as fetch:
        fetch_media()
    fetch.assert_not_called()
    row.refresh_from_db()
    assert (row.status, row.reason) == ('rejected', 'unexpected_media_host')


def test_temporary_download_failure_retries_then_gives_up(house):
    row = drafted(linked(house))
    with patch('apps.notifications.whatsapp.media.get_json',
               side_effect=ProviderRejected('http_503')):
        for _ in range(4):
            WhatsAppMedia.objects.filter(pk=row.pk).update(available_at=timezone.now())
            fetch_media()
    row.refresh_from_db()
    assert (row.status, row.reason, row.attempts) == ('rejected', 'download_failed', 4)


def test_abandoned_files_are_removed(house):
    row = drafted(linked(house))
    WhatsAppMedia.objects.filter(pk=row.pk).update(
        created_at=timezone.now() - timedelta(days=3),
    )
    cleanup_media()
    assert not WhatsAppMedia.objects.filter(pk=row.pk).exists()
