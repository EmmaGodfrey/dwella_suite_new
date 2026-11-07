import hashlib
import hmac
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, connections, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from apps.accounts.access_state import mark_email_verified
from apps.billing.models import Invoice
from apps.billing.services import generate_rent_invoices
from apps.billing.tests import THIS_MONTH, make_lease
from apps.common.provider_http import ProviderRejected
from apps.maintenance.models import MaintenanceRequest
from apps.organizations.models import Organization, OrganizationMembership
from apps.subscriptions.models import WorkspaceAccessPolicy

from .models import NotificationPhoneLink, PhoneMessagingConsent
from .phone_links import receive_link
from .whatsapp.access import actor_context, bind
from .whatsapp.conversation import balance_snapshot, guards_current
from .whatsapp.models import (
    WhatsAppBinding,
    WhatsAppConversation,
    WhatsAppInbound,
    WhatsAppReply,
)
from .whatsapp.transport import apply_reply_status, dispatch_replies
from .whatsapp.worker import _process, cleanup, process_inbox

pytestmark = pytest.mark.django_db
BASE = '/api/v1/notifications/'
PHONE = '+260971234567'


@pytest.fixture(autouse=True)
def config(settings):
    cache.clear()
    settings.WHATSAPP_SELF_SERVICE_ENABLED = True
    settings.WHATSAPP_ENABLED = True
    settings.WHATSAPP_PUBLIC_NUMBER = '+260970000000'
    settings.WHATSAPP_ACCESS_TOKEN = 'synthetic-access'
    settings.WHATSAPP_APP_SECRET = 'synthetic-secret'
    settings.WHATSAPP_VERIFY_TOKEN = 'synthetic-verify'
    settings.WHATSAPP_PHONE_NUMBER_ID = 'number-id'
    settings.WHATSAPP_BUSINESS_ACCOUNT_ID = 'business-id'
    settings.APP_ENVIRONMENT = 'test'
    settings.OUTBOUND_PHONE_ALLOWLIST = [PHONE]


def client(user):
    api = APIClient()
    api.force_authenticate(user)
    return api


@pytest.fixture
def house():
    org = Organization.objects.create(name='WhatsApp workspace')
    tenant = get_user_model().objects.create_user(username='wa-tenant', email='wa@example.com')
    manager = get_user_model().objects.create_user(
        username='wa-manager', email='manager@example.com',
    )
    for user, role in [(tenant, 'tenant'), (manager, 'landlord')]:
        mark_email_verified(user)
        OrganizationMembership.objects.create(organization=org, user=user, role=role)
    lease = make_lease(org)
    lease.tenant.user = tenant
    lease.tenant.save()
    generate_rent_invoices(org, THIS_MONTH)
    return {'org': org, 'tenant': tenant, 'manager': manager, 'lease': lease,
            'invoice': Invoice.objects.get(tenant=lease.tenant)}


def linked(house, role='tenant'):
    user = house[role]
    binding = bind(user, PHONE)
    PhoneMessagingConsent.objects.update_or_create(channel='whatsapp', phone=PHONE, defaults={
        'user': user, 'allowed': False, 'source': 'verified_link',
        'last_inbound_at': timezone.now(), 'granted_at': timezone.now(), 'revoked_at': None,
    })
    return binding


def callback(messages, *, valid=True, number='number-id', business='business-id'):
    raw = json.dumps({'object': 'whatsapp_business_account', 'entry': [{
        'id': business, 'changes': [{'field': 'messages', 'value': {
            'metadata': {'phone_number_id': number}, 'messages': messages,
        }}],
    }]}).encode()
    signature = 'sha256=' + hmac.new(b'synthetic-secret', raw, hashlib.sha256).hexdigest()
    return APIClient().post(BASE + 'webhooks/whatsapp/', raw, content_type='application/json',
                            HTTP_X_HUB_SIGNATURE_256=signature if valid else 'bad')


def incoming(text='menu', *, token=None, phone=PHONE, stamp=None, identity=None):
    identity = identity or f'wamid.{WhatsAppInbound.objects.count() + 1}'
    row = {'id': identity, 'from': phone[1:],
           'timestamp': str(int((stamp or timezone.now()).timestamp()))}
    if token:
        row.update(type='interactive', interactive={
            'type': 'list_reply', 'list_reply': {'id': token},
        })
    else:
        row.update(type='text', text={'body': text})
    assert callback([row]).status_code == 200
    return row


def step(text='menu', token=None):
    incoming(text, token=token)
    process_inbox()
    return WhatsAppReply.objects.latest('pk')


def choose(reply, title):
    return next(row['id'] for row in reply.view['options'] if row['title'] == title)


def workspace(house, role='tenant'):
    linked(house, role)
    reply = step()
    if WhatsAppConversation.objects.get().organization_id:
        return reply
    return step(token=reply.view['options'][0]['id'])


def test_two_sided_link_separates_notification_consent(house):
    api = client(house['tenant'])
    issued = api.post(BASE + 'phone-link/', {'channel': 'whatsapp', 'phone': PHONE,
                                           'actions': True, 'consent': False}, format='json')
    assert issued.status_code == 200, issued.content
    challenge = issued.json()['response_data']
    assert not WhatsAppBinding.objects.exists()
    assert api.post(BASE + 'phone-link/', {'channel': 'whatsapp', 'complete': challenge['id']},
                    format='json').status_code == 400
    assert not receive_link('whatsapp', '+260979999999', challenge['message'], timezone.now())
    assert receive_link('whatsapp', PHONE, challenge['message'], timezone.now())
    assert not WhatsAppBinding.objects.exists()
    result = api.post(BASE + 'phone-link/', {'channel': 'whatsapp', 'complete': challenge['id']},
                      format='json')
    assert result.status_code == 200, result.content
    assert result.json()['response_data']['actions_connected']
    assert WhatsAppBinding.objects.get().user == house['tenant']
    assert not PhoneMessagingConsent.objects.get().allowed
    assert api.post(BASE + 'phone-link/', {'channel': 'whatsapp', 'complete': challenge['id']},
                    format='json').status_code == 400


def test_challenge_cannot_be_completed_by_another_account(house):
    result = client(house['tenant']).post(BASE + 'phone-link/', {
        'channel': 'whatsapp', 'phone': PHONE, 'actions': True,
    }, format='json').json()['response_data']
    receive_link('whatsapp', PHONE, result['message'], timezone.now())
    assert client(house['manager']).post(BASE + 'phone-link/', {
        'channel': 'whatsapp', 'complete': result['id'],
    }, format='json').status_code == 400
    assert not WhatsAppBinding.objects.exists()


def test_pairing_lockout_expiry_and_anonymous_denial(house):
    data = {'channel': 'whatsapp', 'phone': PHONE, 'actions': True}
    assert APIClient().post(BASE + 'phone-link/', data).status_code in {401, 403}
    api = client(house['tenant'])
    issued = api.post(BASE + 'phone-link/', data, format='json').json()['response_data']
    for _ in range(5):
        assert not receive_link('whatsapp', PHONE, 'CONNECT WRONG', timezone.now())
    assert not receive_link('whatsapp', PHONE, issued['message'], timezone.now())
    assert NotificationPhoneLink.objects.get().failed_attempts == 5
    for _ in range(4):
        assert api.post(BASE + 'phone-link/', data, format='json').status_code == 200
    assert api.post(BASE + 'phone-link/', data, format='json').status_code == 429
    NotificationPhoneLink.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert not receive_link('whatsapp', PHONE, issued['message'], timezone.now())


def test_number_conflict_is_generic_and_keeps_original_binding(house):
    original = linked(house)
    with pytest.raises(PermissionDenied, match='This number cannot be connected'):
        bind(house['manager'], PHONE)
    assert WhatsAppBinding.objects.get(revoked_at__isnull=True).pk == original.pk


def test_legacy_notification_link_is_not_action_identity(house):
    api = client(house['tenant'])
    issued = api.post(BASE + 'phone-link/', {'channel': 'whatsapp', 'phone': PHONE,
                                           'consent': True}, format='json').json()['response_data']
    receive_link('whatsapp', PHONE, issued['message'], timezone.now())
    assert api.post(BASE + 'phone-link/', {'channel': 'whatsapp', 'complete': issued['id']},
                    format='json').status_code == 200
    assert not WhatsAppBinding.objects.exists()
    assert 'Connect this number' in step().view['text']


@pytest.mark.parametrize('change', ['unverified', 'inactive', 'admin', 'no_tenancy'])
def test_binding_requires_live_verified_personal_actor(house, change):
    user = house['tenant']
    if change == 'unverified':
        user.account_access_state.delete()
    elif change == 'inactive':
        user.is_active = False
        user.save()
    elif change == 'admin':
        user.is_superuser = True
        user.save()
    else:
        house['lease'].tenant.user = None
        house['lease'].tenant.save()
    with pytest.raises(PermissionDenied):
        bind(user, PHONE)
    assert not WhatsAppBinding.objects.exists()


def test_signed_webhook_dedup_and_malformed_record_isolation(house):
    linked(house)
    row = incoming(identity='same-id')
    assert callback([row]).status_code == 200
    assert WhatsAppInbound.objects.count() == 1
    broken = {**row, 'id': 'broken', 'text': {'body': ['invalid']}}
    valid = {**row, 'id': 'valid'}
    assert callback([broken, valid]).status_code == 200
    assert WhatsAppInbound.objects.get(provider_id='broken').status == 'quarantined'
    assert WhatsAppInbound.objects.get(provider_id='valid').status == 'queued'
    process_inbox()
    count = WhatsAppReply.objects.count()
    process_inbox()
    assert WhatsAppReply.objects.count() == count


@pytest.mark.parametrize('kind', ['signature', 'number', 'business'])
def test_webhook_rejects_forged_identity(house, kind):
    message = {'id': 'forged', 'from': PHONE[1:], 'timestamp': str(int(timezone.now().timestamp())),
               'type': 'text', 'text': {'body': 'balance'}}
    args = {'valid': False} if kind == 'signature' else {kind: 'wrong'}
    result = callback([message], **args)
    assert result.status_code == (403 if kind == 'signature' else 200)
    assert not WhatsAppInbound.objects.exists()


def test_callback_never_sends_and_pairing_token_is_not_retained(house):
    linked(house)
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        incoming('CONNECT PRIVATECODE')
    send.assert_not_called()
    assert WhatsAppInbound.objects.get().payload['text'] == 'connect'


def test_tenant_balance_is_live_and_excludes_other_tenants(house):
    menu = workspace(house)
    other = make_lease(house['org'], unit_name='3B', phone='+260970000002')
    generate_rent_invoices(house['org'], THIS_MONTH)
    other_invoice = Invoice.objects.get(tenant=other.tenant)
    reply = step(token=choose(menu, 'What do I owe?'))
    assert reply.view['guards']['balance']['count'] == 1
    assert reply.view['guards']['balance']['balance'] == str(house['invoice'].balance)
    assert other_invoice.reference not in reply.view['text']
    assert guards_current(actor_context(WhatsAppBinding.objects.get(), house['org'].pk),
                          reply.view['guards'])
    Invoice.objects.filter(pk=house['invoice'].pk).update(amount_paid=1, status='partially_paid')
    assert not guards_current(actor_context(WhatsAppBinding.objects.get(), house['org'].pk),
                              reply.view['guards'])


def test_manager_balance_and_invoice_document_links(house):
    menu = workspace(house, 'manager')
    reply = step(token=choose(menu, 'Invoices'))
    detail = step(token=choose(reply, house['invoice'].reference))
    assert house['invoice'].reference in detail.view['text']
    assert f'billing/invoices/{house["invoice"].public_id}' in detail.view['text']
    assert 'Open securely in Dwella' in detail.view['text']


def test_forged_or_replayed_buttons_cannot_access_records(house):
    menu = workspace(house)
    token = choose(menu, 'What do I owe?')
    first = step(token=token)
    assert 'Outstanding:' in first.view['text']
    second = step(token=token)
    assert 'expired' in second.view['text']
    assert 'Outstanding:' not in second.view['text']
    assert 'expired' in step(token='forged-token').view['text']


def test_multitenancy_requires_explicit_workspace_choice(house):
    other = Organization.objects.create(name='Another workspace')
    OrganizationMembership.objects.create(user=house['manager'], organization=other,
                                          role='landlord')
    linked(house, 'manager')
    reply = step('balance')
    assert reply.view['text'] == 'Choose your workspace.'
    assert len(reply.view['options']) == 2
    assert WhatsAppConversation.objects.get().organization_id is None


def test_stop_revokes_binding_draft_queued_reply_and_pending_challenge(house):
    workspace(house)
    challenge = NotificationPhoneLink.objects.create(user=house['tenant'], channel='whatsapp',
        phone=PHONE, token_hash='fake', expires_at=timezone.now() + timedelta(minutes=5))
    # Ensure STOP is not older than this whole-second challenge creation timestamp.
    incoming('STOP', stamp=timezone.now() + timedelta(seconds=1))
    binding = WhatsAppBinding.objects.get()
    assert binding.revoked_at
    assert WhatsAppConversation.objects.get().draft == {}
    assert not WhatsAppReply.objects.filter(status='queued').exists()
    challenge.refresh_from_db()
    assert challenge.consumed_at
    consent = PhoneMessagingConsent.objects.get()
    assert not consent.allowed and consent.revoked_at


def test_disconnect_and_reconnect_invalidate_old_events(house):
    linked(house)
    incoming('balance')
    assert client(house['tenant']).delete(BASE + 'phone-link/').status_code == 200
    linked(house)
    process_inbox()
    assert WhatsAppInbound.objects.get().reason == 'old_binding_event'
    assert not WhatsAppReply.objects.exists()


@pytest.mark.parametrize('change', ['password', 'email', 'reverification', 'suspended',
                                  'membership', 'tenant_unlinked', 'feature'])
def test_delayed_replies_recheck_current_access(house, change):
    menu = workspace(house)
    step(token=choose(menu, 'What do I owe?'))
    if change == 'password':
        house['tenant'].set_password('a-new-test-password')
        house['tenant'].save()
    elif change == 'email':
        house['tenant'].email = 'changed@example.com'
        house['tenant'].save()
    elif change == 'reverification':
        mark_email_verified(house['tenant'])
    elif change == 'suspended':
        house['org'].is_active = False
        house['org'].save()
    elif change == 'membership':
        OrganizationMembership.objects.filter(user=house['tenant']).update(is_active=False)
    elif change == 'tenant_unlinked':
        house['lease'].tenant.user = None
        house['lease'].tenant.save()
    else:
        WorkspaceAccessPolicy.objects.create(organization=house['org'],
            feature_overrides={'whatsapp_messages': {'enabled': False}})
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        dispatch_replies()
    send.assert_not_called()
    assert WhatsAppReply.objects.latest('pk').status == 'cancelled'


def test_unknown_sender_profile_number_does_not_grant_access(house):
    house['lease'].tenant.phone_number = PHONE
    house['lease'].tenant.save()
    reply = step('balance')
    assert not reply.binding_id
    assert 'Connect this number' in reply.view['text']
    assert house['invoice'].reference not in reply.view['text']


def test_deleted_binding_never_turns_sensitive_reply_into_guest_reply(house):
    menu = workspace(house)
    reply = step(token=choose(menu, 'What do I owe?'))
    WhatsAppBinding.objects.get().delete()
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        dispatch_replies()
    send.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == 'cancelled' and reply.reason == 'binding_removed'


def test_missing_workspace_cancels_sensitive_reply(house):
    menu = workspace(house)
    reply = step(token=choose(menu, 'What do I owe?'))
    WhatsAppReply.objects.filter(pk=reply.pk).update(organization=None)
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        dispatch_replies()
    send.assert_not_called()
    reply.refresh_from_db()
    assert reply.reason == 'workspace_removed'


def test_stale_and_out_of_order_events_do_not_execute(house):
    linked(house)
    incoming(stamp=timezone.now() - timedelta(hours=25))
    process_inbox()
    assert not WhatsAppReply.objects.exists()
    step()
    incoming(stamp=timezone.now() - timedelta(minutes=1))
    process_inbox()
    assert WhatsAppInbound.objects.latest('pk').reason == 'out_of_order'


def test_tenant_repair_requires_explicit_confirmation_and_is_idempotent(house):
    menu = workspace(house)
    reply = step(token=choose(menu, 'Report a repair'))
    step(token=reply.view['options'][0]['id'])
    step('Tap leaking')
    reply = step('Water leaks below the kitchen tap.')
    reply = step(token=choose(reply, 'Contact me first'))
    assert not MaintenanceRequest.objects.exists()
    token = choose(reply, 'Confirm repair')
    result = step(token=token)
    job = MaintenanceRequest.objects.get()
    assert job.tenant == house['lease'].tenant and job.reported_by == house['tenant']
    assert not job.permission_to_enter
    assert 'submitted' in result.view['text']
    step(token=token)
    assert MaintenanceRequest.objects.count() == 1


def test_repair_back_cancels_draft_without_opt_out(house):
    menu = workspace(house)
    reply = step(token=choose(menu, 'Report a repair'))
    step(token=reply.view['options'][0]['id'])
    step('Title')
    step('BACK')
    assert WhatsAppConversation.objects.get().draft == {}
    assert WhatsAppBinding.objects.get().revoked_at is None
    assert not MaintenanceRequest.objects.exists()


def test_failed_processing_rolls_back_domain_write_then_advances_other_events(house):
    linked(house)
    incoming(identity='bad')
    incoming(identity='good')
    from .whatsapp.conversation import handle as real

    def handle(binding, conversation, event):
        if event.provider_id == 'bad':
            Invoice.objects.filter(pk=house['invoice'].pk).update(notes='must roll back')
            raise RuntimeError('Private message detail')
        return real(binding, conversation, event)

    with patch('apps.notifications.whatsapp.worker.handle', side_effect=handle):
        process_inbox()
    house['invoice'].refresh_from_db()
    assert house['invoice'].notes == ''
    assert WhatsAppInbound.objects.get(provider_id='bad').attempts == 1
    assert WhatsAppInbound.objects.get(provider_id='good').status == 'done'


@pytest.mark.parametrize('error,status', [(TimeoutError(), 'review'),
                                         (ProviderRejected('http_500'), 'review'),
                                         (ProviderRejected('http_400'), 'failed')])
def test_uncertain_send_is_never_blindly_retried(house, error, status):
    linked(house)
    step()
    with patch('apps.notifications.whatsapp.transport.post_json', side_effect=error) as send:
        dispatch_replies()
        dispatch_replies()
    assert send.call_count == 1
    assert WhatsAppReply.objects.get().status == status


def test_delivery_callback_racing_send_response_preserves_read(house):
    linked(house)
    reply = step()

    def send(*args):
        with transaction.atomic():
            apply_reply_status({'id': 'wamid.accepted', 'status': 'read',
                                'recipient_id': PHONE[1:],
                                'biz_opaque_callback_data': str(reply.public_id)}, timezone.now())
        return {'messages': [{'id': 'wamid.accepted'}]}

    with patch('apps.notifications.whatsapp.transport.post_json', side_effect=send):
        assert dispatch_replies() == 1
    reply.refresh_from_db()
    assert reply.status == 'read' and reply.provider_id == 'wamid.accepted'


def test_disabled_switch_allowlist_and_reply_window(house, settings):
    linked(house)
    step()
    settings.OUTBOUND_PHONE_ALLOWLIST = []
    with patch('apps.notifications.whatsapp.transport.post_json') as send:
        dispatch_replies()
    send.assert_not_called()
    assert WhatsAppReply.objects.get().reason == 'recipient_restricted'
    settings.WHATSAPP_SELF_SERVICE_ENABLED = False
    assert process_inbox() == dispatch_replies() == 0


def test_money_adapter_continuation_receives_only_current_actor_choices(house):
    menu = workspace(house)
    adapter = Mock()

    def start(ctx, conversation, intent, target):
        from .whatsapp.conversation import choice, response

        assert ctx.user == house['tenant'] and intent == 'payment_proof'
        conversation.draft = {'intent': intent}
        return response('Enter the payment reference.', [choice(
            conversation, 'Confirm submission', 'proof_confirm', member=ctx.membership,
        )])

    adapter.start.side_effect = start
    adapter.handle.return_value = {'text': 'Handled by the money adapter.',
                                   'options': [], 'guards': {}}
    with patch('apps.notifications.whatsapp.conversation.MONEY_ADAPTER', adapter):
        reply = step(token=choose(menu, 'I have already paid'))
        step(token=choose(reply, 'Confirm submission'))
    assert adapter.start.call_count == adapter.handle.call_count == 1
    assert adapter.handle.call_args.args[3]['action'] == 'proof_confirm'


@pytest.mark.parametrize('body', [[], 'bad', {'channel': 'whatsapp', 'phone': 'invalid',
                                           'actions': True}])
def test_malformed_link_body_returns_validation_error(house, body):
    result = client(house['tenant']).post(BASE + 'phone-link/', body, format='json')
    assert result.status_code == 400
    assert not WhatsAppBinding.objects.exists()


def test_cleanup_clears_content_then_keeps_dedupe_tombstones(house):
    linked(house)
    incoming()
    WhatsAppInbound.objects.update(received_at=timezone.now() - timedelta(days=31))
    cleanup()
    assert WhatsAppInbound.objects.get().payload == {}
    WhatsAppInbound.objects.update(received_at=timezone.now() - timedelta(days=91))
    cleanup()
    assert not WhatsAppInbound.objects.exists()


def test_balance_query_budget_is_independent_of_invoice_count(house):
    binding = linked(house, 'manager')
    ctx = actor_context(binding, house['org'].pk)
    with CaptureQueriesContext(connection) as small:
        balance_snapshot(ctx)
    for index in range(12):
        make_lease(house['org'], unit_name=f'Unit {index}', phone=f'+26097000{index:04d}')
    generate_rent_invoices(house['org'], THIS_MONTH)
    with CaptureQueriesContext(connection) as full:
        balance_snapshot(ctx)
    assert len(small) == len(full) == 1


@pytest.mark.skipif(connection.vendor != 'postgresql', reason='PostgreSQL RLS only')
def test_private_whatsapp_tables_have_rls():
    tables = ['notifications_whatsappbinding', 'notifications_whatsappinbound',
              'notifications_whatsappconversation', 'notifications_whatsappreply',
              'notifications_whatsappmedia', 'notifications_whatsappproofnotice']
    with connection.cursor() as cursor:
        cursor.execute('SELECT relname, relrowsecurity FROM pg_class WHERE relname = ANY(%s)',
                       [tables])
        actual = dict(cursor.fetchall())
    assert actual == dict.fromkeys(tables, True)


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != 'postgresql', reason='Real concurrent row locks')
def test_competing_workers_process_same_event_once(house):
    linked(house)
    incoming()
    pk = WhatsAppInbound.objects.get().pk

    def work():
        try:
            _process(pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: work(), range(2)))
    assert WhatsAppReply.objects.count() == 1
    assert WhatsAppInbound.objects.get().status == 'done'


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != 'postgresql', reason='Real concurrent row locks')
def test_competing_senders_send_once_without_holding_transaction(house):
    linked(house)
    step()

    def send(*args):
        assert not connection.in_atomic_block
        return {'messages': [{'id': 'wamid.once'}]}

    def work():
        try:
            return dispatch_replies()
        finally:
            connections.close_all()

    with patch('apps.notifications.whatsapp.transport.post_json', side_effect=send) as sender:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: work(), range(2)))
    assert sum(results) == 1 and sender.call_count == 1
    assert WhatsAppReply.objects.get().status == 'sent'
