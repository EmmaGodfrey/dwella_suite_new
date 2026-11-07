# ruff: noqa: F811
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.access_state import mark_email_verified
from apps.organizations.models import Organization, OrganizationMembership
from apps.subscriptions.models import WorkspaceAccessPolicy

from .models import PhoneMessagingConsent
from .test_whatsapp import (  # noqa: F401
    PHONE,
    choose,
    client,
    config,
    house,
    incoming,
    linked,
    step,
    workspace,
)
from .whatsapp.models import WhatsAppBinding, WhatsAppConversation, WhatsAppReply
from .whatsapp.recovery import STOP_ACK, workspace_options
from .whatsapp.transport import dispatch_replies
from .whatsapp.worker import process_inbox

pytestmark = pytest.mark.django_db


def test_single_workspace_opens_menu_and_balance_without_picker(house):
    linked(house)
    reply = step('Hi')
    assert 'How can Dwella help?' in reply.view['text']
    assert WhatsAppConversation.objects.get().organization_id == house['org'].pk
    reply = step('balance')
    assert 'Outstanding:' in reply.view['text']


def test_expired_single_workspace_returns_to_own_menu(house):
    workspace(house)
    WhatsAppConversation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    reply = step('Hi')
    assert 'How can Dwella help?' in reply.view['text']
    assert not WhatsAppBinding.objects.get().revoked_at


def test_expired_button_returns_current_menu_without_workspace_picker(house):
    reply = workspace(house)
    token = choose(reply, 'What do I owe?')
    WhatsAppConversation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    result = step(token=token)
    assert 'expired' in result.view['text']
    assert choose(result, 'What do I owe?')
    assert 'Outstanding:' not in result.view['text']
    assert WhatsAppConversation.objects.get().organization_id == house['org'].pk


def test_voided_invoice_returns_to_menu_without_revoking_binding(house):
    menu = workspace(house)
    listing = step(token=choose(menu, 'My invoices'))
    house['invoice'].status = 'void'
    house['invoice'].save()
    reply = step(token=choose(listing, house['invoice'].reference))
    assert 'no longer available' in reply.view['text']
    assert choose(reply, 'What do I owe?')
    assert not WhatsAppBinding.objects.get().revoked_at
    with patch('apps.notifications.whatsapp.transport.post_json',
               return_value={'messages': [{'id': 'recovered'}]}) as sender:
        assert dispatch_replies() == 1
    assert sender.call_count == 1


@pytest.mark.parametrize('failure', ['unlinked', 'suspended', 'feature', 'membership'])
def test_unavailable_workspace_keeps_identity_and_explains_recovery(house, failure):
    workspace(house)
    if failure == 'unlinked':
        house['lease'].tenant.user = None
        house['lease'].tenant.save()
    elif failure == 'suspended':
        house['org'].is_active = False
        house['org'].save()
    elif failure == 'feature':
        WorkspaceAccessPolicy.objects.create(organization=house['org'], feature_overrides={
            'whatsapp_messages': {'enabled': False},
        })
    else:
        OrganizationMembership.objects.filter(user=house['tenant']).update(is_active=False)
    reply = step('balance')
    assert 'no longer available' in reply.view['text']
    assert not WhatsAppBinding.objects.get().revoked_at
    assert WhatsAppConversation.objects.get().organization_id is None
    assert not reply.view['options']


def test_unlinked_tenant_membership_is_not_offered(house):
    other = Organization.objects.create(name='Unlinked workspace')
    OrganizationMembership.objects.create(organization=other, user=house['tenant'], role='tenant')
    linked(house)
    reply = step()
    assert WhatsAppConversation.objects.get().organization_id == house['org'].pk
    assert 'Unlinked workspace' not in reply.view['text']


def test_reconnect_notice_has_its_own_budget_after_linked_messages(house):
    workspace(house)
    step('balance')
    house['tenant'].set_password('a-new-synthetic-password')
    house['tenant'].save()
    reply = step('menu')
    assert WhatsAppBinding.objects.get().revoked_at
    assert reply.view['notice'] == 'reconnect' and reply.status == 'queued'
    with patch('apps.notifications.whatsapp.transport.post_json',
               return_value={'messages': [{'id': 'reconnect'}]}) as sender:
        dispatch_replies()
    assert sender.call_count == 1
    assert 'Reconnect' in sender.call_args.args[1]['text']['body']


def test_reverification_revokes_identity_but_not_record_failure(house):
    workspace(house)
    mark_email_verified(house['tenant'])
    reply = step('balance')
    assert WhatsAppBinding.objects.get().revoked_at
    assert reply.view['notice'] == 'reconnect'


def test_guest_instruction_does_not_consume_reconnect_notice_budget(house):
    reply = step()
    assert reply.view['notice'] == 'connect'
    linked(house)
    step()
    house['tenant'].set_password('new-synthetic-password')
    house['tenant'].save()
    reply = step()
    assert reply.view['notice'] == 'reconnect'


def test_stop_gets_one_fixed_confirmation_without_restoring_consent(house):
    workspace(house)
    incoming('STOP', stamp=timezone.now() + timedelta(seconds=1))
    process_inbox()
    reply = WhatsAppReply.objects.latest('pk')
    assert reply.view['text'] == STOP_ACK and reply.view['notice'] == 'stop_ack'
    assert not reply.binding_id and not reply.organization_id
    with patch('apps.notifications.whatsapp.transport.post_json',
               return_value={'messages': [{'id': 'stop-ack'}]}) as sender:
        assert dispatch_replies() == 1
    assert sender.call_count == 1
    assert not PhoneMessagingConsent.objects.get().allowed
    assert PhoneMessagingConsent.objects.get().revoked_at
    assert WhatsAppBinding.objects.get().revoked_at
    count = WhatsAppReply.objects.count()
    incoming('STOP', stamp=timezone.now() + timedelta(seconds=2))
    process_inbox()
    assert WhatsAppReply.objects.count() == count


@pytest.mark.parametrize('tamper', ['body', 'options', 'evidence', 'old_number',
                                  'outside_allowlist', 'window'])
def test_stop_confirmation_cannot_bypass_normal_transport_boundaries(house, settings, tamper):
    workspace(house)
    incoming('STOP', stamp=timezone.now() + timedelta(seconds=1))
    process_inbox()
    reply = WhatsAppReply.objects.latest('pk')
    if tamper == 'body':
        reply.view['text'] = 'Sensitive account details'
        reply.save()
    elif tamper == 'options':
        reply.view['options'] = [{'id': 'bad', 'title': 'Approve money'}]
        reply.save()
    elif tamper == 'evidence':
        reply.view['evidence'] = ['private-document-id']
        reply.save()
    elif tamper == 'old_number':
        settings.WHATSAPP_PHONE_NUMBER_ID = 'different-number'
    elif tamper == 'outside_allowlist':
        settings.OUTBOUND_PHONE_ALLOWLIST = []
    else:
        PhoneMessagingConsent.objects.update(last_inbound_at=timezone.now() - timedelta(hours=25))
    with patch('apps.notifications.whatsapp.transport.post_json') as sender:
        dispatch_replies()
    sender.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == 'cancelled'


def test_queued_stop_ack_is_cancelled_after_reconnection(house):
    workspace(house)
    incoming('STOP', stamp=timezone.now() + timedelta(seconds=1))
    process_inbox()
    linked(house)
    with patch('apps.notifications.whatsapp.transport.post_json') as sender:
        dispatch_replies()
    sender.assert_not_called()


def test_workspace_options_have_constant_query_count(house):
    binding = linked(house, 'manager')
    conversation = WhatsAppConversation.objects.create(binding=binding,
                                                        generation=binding.generation)
    with CaptureQueriesContext(connection) as small:
        workspace_options(binding, conversation)
    for index in range(7):
        other = Organization.objects.create(name=f'Other workspace {index}')
        OrganizationMembership.objects.create(organization=other, user=house['manager'],
                                              role='landlord')
    with CaptureQueriesContext(connection) as full:
        workspace_options(binding, conversation)
    assert len(small) == len(full)
