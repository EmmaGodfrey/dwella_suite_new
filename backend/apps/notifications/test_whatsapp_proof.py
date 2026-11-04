"""The guided WhatsApp payment-proof flow, end to end through signed webhooks."""
import pytest

from . import test_whatsapp as base
from .models import PhoneMessagingConsent
from .test_whatsapp import PHONE, choose, incoming, step, workspace
from .whatsapp.models import WhatsAppBinding, WhatsAppInbound, WhatsAppReply
from .whatsapp.worker import process_inbox

pytestmark = pytest.mark.django_db
config = base.config
house = base.house


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
