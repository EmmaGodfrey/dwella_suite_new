"""Approved-template proof messages: who gets them and when they must not go out."""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.billing import proofs

from . import test_whatsapp as base
from .models import PhoneMessagingConsent
from .test_whatsapp import PHONE
from .whatsapp.access import bind, revoke
from .whatsapp.models import WhatsAppProofNotice
from .whatsapp.notices import dispatch_proof_notices, token_hash

pytestmark = pytest.mark.django_db
config = base.config
house = base.house
TENANT_PHONE = '+260971234568'
TEMPLATES = ['dwella_payment_proof_review:en', 'dwella_payment_received:en',
             'dwella_payment_proof_declined:en', 'dwella_payment_proof_question:en']
POST = 'apps.notifications.whatsapp.notices.post_json'


@pytest.fixture(autouse=True)
def approved(settings, config):
    settings.APPROVED_WHATSAPP_TEMPLATES = TEMPLATES
    settings.WHATSAPP_TEMPLATE_LANGUAGE = 'en'
    settings.OUTBOUND_PHONE_ALLOWLIST = [PHONE, TENANT_PHONE]


def connect(user, phone, allowed=True):
    binding = bind(user, phone)
    PhoneMessagingConsent.objects.update_or_create(channel='whatsapp', phone=phone, defaults={
        'user': user, 'allowed': allowed, 'source': 'verified_link',
        'last_inbound_at': timezone.now(), 'granted_at': timezone.now(), 'revoked_at': None,
    })
    return binding


def report(house):
    return proofs.submit(
        house['invoice'], user=house['tenant'], amount=Decimal('100'), method='mobile_money',
        paid_on=timezone.localdate(), reference='MP1',
    )


def sent(response='wamid.sent'):
    return patch(POST, return_value={'messages': [{'id': response}]})


def test_review_goes_to_connected_manager_with_private_action_buttons(house):
    connect(house['manager'], PHONE)
    proof = report(house)
    with sent() as post:
        assert dispatch_proof_notices() == 1
    body = post.call_args.args[1]
    assert body['template']['name'] == 'dwella_payment_proof_review'
    assert [row['text'] for row in body['template']['components'][0]['parameters']][-1] == (
        proof.number
    )
    buttons = body['template']['components'][1:]
    assert [row['index'] for row in buttons] == ['0', '1', '2']
    payloads = [row['parameters'][0]['payload'] for row in buttons]
    assert [row.split('.')[1] for row in payloads] == ['review', 'reject', 'ask']
    notice = WhatsAppProofNotice.objects.get()
    token = payloads[0].split('.', 2)[2]
    assert notice.status == 'sent' and notice.token_hash == token_hash(token)
    assert token not in str(notice.__dict__)


def test_tenant_is_told_each_outcome(house):
    connect(house['tenant'], TENANT_PHONE)
    proof = report(house)
    proofs.decline(proof, user=house['manager'], note='Which account?', ask=True)
    with sent() as post:
        dispatch_proof_notices()
    assert post.call_args.args[1]['template']['name'] == 'dwella_payment_proof_question'
    proof = proofs.resubmit(proof, user=house['tenant'], amount=Decimal('100'),
                            method='mobile_money', paid_on=timezone.localdate(), reference='MP2')
    proofs.confirm(proof, user=house['manager'])
    with sent() as post:
        dispatch_proof_notices()
    assert post.call_args.args[1]['template']['name'] == 'dwella_payment_received'


@pytest.mark.parametrize('change,reason', [
    (lambda house, proof: proofs.confirm(proof, user=house['manager']), 'proof_changed'),
    (lambda house, proof: revoke(user=house['manager']), 'binding_changed'),
    (lambda house, proof: PhoneMessagingConsent.objects.update(allowed=False),
     'recipient_opted_out'),
    (lambda house, proof: WhatsAppProofNotice.objects.update(
        expires_at=timezone.now() - timedelta(minutes=1)), 'expired'),
])
def test_stale_review_is_not_sent(house, change, reason):
    connect(house['manager'], PHONE)
    proof = report(house)
    change(house, proof)
    with sent() as post:
        dispatch_proof_notices()
    post.assert_not_called()
    assert WhatsAppProofNotice.objects.get(purpose='review').reason == reason


def test_unapproved_template_is_not_sent_and_proof_still_stands(house, settings):
    settings.APPROVED_WHATSAPP_TEMPLATES = []
    connect(house['manager'], PHONE)
    proof = report(house)
    with sent() as post:
        dispatch_proof_notices()
    post.assert_not_called()
    assert WhatsAppProofNotice.objects.get().reason == 'template_required'
    assert proof.status == 'submitted'


def test_disabled_switch_queues_nothing(house, settings):
    settings.WHATSAPP_SELF_SERVICE_ENABLED = False
    connect(house['manager'], PHONE)
    report(house)
    assert not WhatsAppProofNotice.objects.exists()


def test_uncertain_send_is_never_retried(house):
    connect(house['manager'], PHONE)
    report(house)
    with patch(POST, side_effect=TimeoutError) as post:
        dispatch_proof_notices()
        dispatch_proof_notices()
    assert post.call_count == 1
    assert WhatsAppProofNotice.objects.get().status == 'review'


def test_cash_needs_no_file_or_reference_but_other_methods_do(house):
    proof = proofs.submit(house['invoice'], user=house['tenant'], amount=Decimal('100'),
                          method='cash', paid_on=timezone.localdate())
    assert proof.status == 'submitted'
    with pytest.raises(ValidationError):
        proofs.submit(house['invoice'], user=house['tenant'], amount=Decimal('100'),
                      method='bank_transfer', paid_on=timezone.localdate())
