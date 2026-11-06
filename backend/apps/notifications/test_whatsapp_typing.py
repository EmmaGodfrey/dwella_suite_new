"""Typing status is guarded, bounded and independent of payment/reply delivery."""
import json
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import pytest
from django.db import connection
from django.utils import timezone

from . import test_whatsapp as base
from .models import PhoneMessagingConsent
from .test_whatsapp import incoming, linked, step
from .whatsapp.transport import dispatch_replies
from .whatsapp.typing import NoRedirect, indicate

pytestmark = pytest.mark.django_db(transaction=True)
config = base.config
house = base.house


@pytest.fixture(autouse=True)
def typing_enabled(settings):
    settings.WHATSAPP_TYPING_ENABLED = True


def status_response():
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = b'{"success":true}'
    return response


def test_typing_uses_real_inbound_id_after_commit_and_before_reply(house):
    linked(house)
    reply = step()
    order = []

    def status(request, *, timeout):
        assert not connection.in_atomic_block
        assert timeout == 0.5
        payload = json.loads(request.data)
        assert payload == {
            'messaging_product': 'whatsapp', 'status': 'read',
            'message_id': reply.inbound.provider_id, 'typing_indicator': {'type': 'text'},
        }
        assert 'synthetic-access' in request.headers['Authorization']
        order.append('typing')
        return status_response()

    def send(*args):
        order.append('reply')
        return {'messages': [{'id': 'wamid.reply'}]}

    with patch('apps.notifications.whatsapp.typing.opener.open', side_effect=status), patch(
        'apps.notifications.whatsapp.transport.post_json', side_effect=send,
    ):
        assert dispatch_replies() == 1
    assert order == ['typing', 'reply']


@pytest.mark.parametrize('failure', [TimeoutError(), HTTPError('https://graph.facebook.com',
                          400, 'rejected', {}, None), ValueError('invalid response')])
def test_typing_failure_never_marks_actual_reply_uncertain_or_retries(house, failure):
    linked(house)
    reply = step()
    with (
        patch('apps.notifications.whatsapp.typing.opener.open', side_effect=failure) as status,
        patch('apps.notifications.whatsapp.transport.post_json',
              return_value={'messages': [{'id': 'wamid.reply'}]}) as send,
    ):
        assert dispatch_replies() == 1
    assert status.call_count == send.call_count == 1
    reply.refresh_from_db()
    assert reply.status == 'sent'


def test_disabled_feature_does_not_add_status_io(house, settings):
    settings.WHATSAPP_TYPING_ENABLED = False
    linked(house)
    reply = step()
    with patch('apps.notifications.whatsapp.typing.opener.open') as status:
        assert not indicate(reply)
    status.assert_not_called()


def test_status_request_construction_failure_still_allows_reply(house):
    linked(house)
    step()
    with patch('apps.notifications.whatsapp.typing.Request', side_effect=ValueError), patch(
        'apps.notifications.whatsapp.transport.post_json',
        return_value={'messages': [{'id': 'wamid.reply'}]},
    ) as send:
        assert dispatch_replies() == 1
    send.assert_called_once()


def test_unlinked_and_stop_ack_never_emit_typing(house):
    incoming('Hi')
    from .whatsapp.models import WhatsAppReply
    from .whatsapp.worker import process_inbox

    process_inbox()
    reply = WhatsAppReply.objects.get()
    with patch('apps.notifications.whatsapp.typing.opener.open') as status:
        assert not indicate(reply)
    status.assert_not_called()
    linked(house)
    reply = step()
    reply.view['notice'] = 'stop_ack'
    with patch('apps.notifications.whatsapp.typing.opener.open') as status:
        assert not indicate(reply)
    status.assert_not_called()


def test_opt_out_before_claim_emits_neither_status_nor_reply(house):
    linked(house)
    step()
    PhoneMessagingConsent.objects.update(revoked_at=timezone.now())
    with patch('apps.notifications.whatsapp.typing.opener.open') as status, patch(
        'apps.notifications.whatsapp.transport.post_json',
    ) as send:
        assert dispatch_replies() == 0
    status.assert_not_called()
    send.assert_not_called()


def test_opt_out_during_typing_prevents_reply(house):
    linked(house)
    reply = step()

    def status(*args, **kwargs):
        PhoneMessagingConsent.objects.update(revoked_at=timezone.now())
        return status_response()

    with patch('apps.notifications.whatsapp.typing.opener.open', side_effect=status), patch(
        'apps.notifications.whatsapp.transport.post_json',
    ) as send:
        assert dispatch_replies() == 0
    send.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == 'cancelled'


def test_status_redirects_are_refused():
    assert NoRedirect().redirect_request(None, None, 302, '', {}, 'https://unexpected.test') is None
