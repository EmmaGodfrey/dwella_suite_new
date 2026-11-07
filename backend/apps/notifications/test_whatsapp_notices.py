"""Approved-template proof messages: who gets them and when they must not go out."""
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.access_state import mark_email_verified
from apps.billing import proofs
from apps.organizations.models import OrganizationMembership

from . import test_whatsapp as base
from .models import PhoneMessagingConsent
from .money_templates import covered_by_proof_notice
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


def second_manager(house):
    other = get_user_model().objects.create_user(username='second-reviewer', email='r2@example.com')
    mark_email_verified(other)
    return other, OrganizationMembership.objects.create(
        organization=house['invoice'].organization, user=other, role='landlord',
    )


def choose(house, membership):
    workspace = house['invoice'].organization
    workspace.proof_reviewer = membership
    workspace.save(update_fields=['proof_reviewer'])


def test_chosen_reviewer_alone_gets_the_review_message(house):
    connect(house['manager'], PHONE)
    other, membership = second_manager(house)
    binding = connect(other, '+260971234569')
    choose(house, membership)
    report(house)
    assert [row.binding_id for row in WhatsAppProofNotice.objects.all()] == [binding.pk]


def test_review_reaches_all_managers_without_a_usable_reviewer(house):
    connect(house['manager'], PHONE)
    other, membership = second_manager(house)
    # Chosen, but never connected WhatsApp.
    choose(house, membership)
    report(house)
    assert WhatsAppProofNotice.objects.count() == 1
    # Chosen and connected, then removed: they get nothing, and the others still do.
    connect(other, '+260971234569')
    membership.is_active = False
    membership.save(update_fields=['is_active'])
    proof = report(house)
    notice = WhatsAppProofNotice.objects.get(proof=proof)
    assert notice.binding.user == house['manager']


def test_manager_whatsapp_notice_steps_aside_for_the_review_message(house):
    unconnected = report(house)
    row = SimpleNamespace(event='proof.submitted', audience='manager', target_id=unconnected.pk)
    # Nobody received a review message, so the ordinary notice must still go out.
    assert not covered_by_proof_notice(row)
    connect(house['manager'], PHONE)
    row.target_id = report(house).pk
    assert covered_by_proof_notice(row)
    WhatsAppProofNotice.objects.update(status='cancelled')
    assert not covered_by_proof_notice(row)


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
