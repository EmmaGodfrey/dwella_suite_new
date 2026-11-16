"""Assigned managers pair without a tenancy and keep website-equivalent read scope."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.accounts.access_state import mark_email_verified
from apps.billing.models import Invoice, Payment
from apps.billing.services import generate_rent_invoices, record_payment
from apps.billing.tests import THIS_MONTH, make_lease
from apps.maintenance.models import MaintenanceRequest
from apps.organizations.models import (
    CoverSession,
    Organization,
    OrganizationMembership,
    PropertyAssignment,
)
from apps.properties.models import Property

from . import test_whatsapp as base
from .models import NotificationPhoneLink
from .phone_links import receive_link
from .whatsapp.access import actor_context, bind
from .whatsapp.conversation import run_action
from .whatsapp.documents import available, descriptor, source
from .whatsapp.models import WhatsAppBinding, WhatsAppConversation
from .whatsapp.recovery import eligible_memberships
from .whatsapp.transport import block, dispatch_replies

pytestmark = pytest.mark.django_db
config = base.config
house = base.house


@pytest.fixture
def managed(house):
    user = get_user_model().objects.create_user(
        username='assigned-manager', email='assigned@example.com',
    )
    mark_email_verified(user)
    member = OrganizationMembership.objects.create(
        user=user, organization=house['org'], role='manager',
    )
    assignment = PropertyAssignment.objects.create(
        organization=house['org'], membership=member, property=house['lease'].unit.property,
    )
    other_lease = make_lease(house['org'], unit_name='Other', phone='+260979999999', rent='2600')
    other_property = Property.objects.create(
        organization=house['org'], name='Unassigned home', property_type='house', address='Plot 2',
    )
    other_lease.unit.property = other_property
    other_lease.unit.save(update_fields=['property'])
    generate_rent_invoices(house['org'], THIS_MONTH)
    other_invoice = Invoice.objects.get(lease=other_lease)
    house.update(assigned=user, member=member, assignment=assignment,
                 other_property=other_property, other_invoice=other_invoice)
    return house


def context(house):
    return actor_context(bind(house['assigned'], base.PHONE), house['org'].pk)


def test_manager_completes_real_pairing_without_a_tenant_record(managed):
    api = base.client(managed['assigned'])
    response = api.post(base.BASE + 'phone-link/', {
        'channel': 'whatsapp', 'phone': base.PHONE, 'actions': True, 'consent': False,
    }, format='json')
    assert response.status_code == 200
    challenge = response.json()['response_data']
    assert receive_link('whatsapp', base.PHONE, challenge['message'], timezone.now())
    response = api.post(base.BASE + 'phone-link/', {
        'channel': 'whatsapp', 'complete': challenge['id'],
    }, format='json')
    assert response.status_code == 200, response.content
    assert WhatsAppBinding.objects.get().user == managed['assigned']
    assert NotificationPhoneLink.objects.get(pk=challenge['id']).consumed_at
    assert eligible_memberships(managed['assigned']).get() == managed['member']
    assert not managed['assigned'].tenant_records.exists()


def test_manager_with_no_assignments_can_connect_but_reads_no_property_records(managed):
    managed['assignment'].delete()
    ctx = context(managed)
    assert not ctx.scope(Invoice.objects.all()).exists()
    menu = base.workspace(managed, 'assigned')
    assert 'No properties are assigned to you' in menu.view['text']
    reply = base.step(token=base.choose(menu, 'Invoices'))
    assert 'There are no records' in reply.view['text']


def test_manager_balance_and_lists_exclude_other_properties(managed):
    menu = base.workspace(managed, 'assigned')
    assert 'Assigned properties only' in menu.view['text']
    reply = base.step(token=base.choose(menu, 'Who owes me?'))
    assert 'Assigned-property open invoices: 1' in reply.view['text']
    assert '3,900.00' in reply.view['text'] and '6,500.00' not in reply.view['text']
    menu = base.step('MENU')
    listing = base.step(token=base.choose(menu, 'Invoices'))
    titles = [item['title'] for item in listing.view['options']]
    assert managed['invoice'].reference in titles
    assert managed['other_invoice'].reference not in titles


@pytest.mark.parametrize('kind', ['invoice', 'receipt', 'repair'])
def test_manager_cannot_select_an_unassigned_record_or_pdf(managed, kind):
    ctx = context(managed)
    target = managed['other_invoice'].public_id
    model_kind = kind
    if kind == 'receipt':
        payment = record_payment(
            invoice=managed['other_invoice'], amount=Decimal('100'), method='cash',
            paid_on=timezone.localdate(), recorded_by=managed['manager'],
        )
        target = payment.public_id
    elif kind == 'repair':
        row = MaintenanceRequest.objects.create(
            organization=managed['org'], property=managed['other_property'],
            reference='REQ-OTHER', title='Private repair',
        )
        target = row.public_id
    conversation = WhatsAppConversation.objects.create(binding=ctx.binding)
    with pytest.raises(PermissionDenied):
        run_action(ctx, conversation, kind, target)
    if kind != 'repair':
        document = descriptor(model_kind, target, managed['org'])
        assert not available(ctx, document)
        with pytest.raises(PermissionDenied):
            source(ctx, document)


def test_manager_can_request_assigned_invoice_and_receipt_sources(managed):
    payment = record_payment(
        invoice=managed['invoice'], amount=Decimal('100'), method='cash',
        paid_on=timezone.localdate(), recorded_by=managed['manager'],
    )
    ctx = context(managed)
    for kind, row in [('invoice', managed['invoice']), ('receipt', payment)]:
        document = descriptor(kind, row.public_id, managed['org'])
        assert available(ctx, document)
        assert source(ctx, document)['reference'] in {row.reference, payment.receipt_number}


def test_assignment_removal_blocks_queued_reply_and_stale_button(managed):
    menu = base.workspace(managed, 'assigned')
    listing = base.step(token=base.choose(menu, 'Invoices'))
    token = base.choose(listing, managed['invoice'].reference)
    assert not block(listing)
    managed['assignment'].delete()
    assert block(listing) == 'access_or_target_changed'
    reply = base.step(token=token)
    assert managed['invoice'].reference not in reply.view['text']
    assert not context(managed).scope(Invoice.objects.all()).exists()


def test_role_demotion_blocks_previously_queued_owner_data(managed):
    member = managed['member']
    member.role = 'landlord'
    member.save()
    menu = base.workspace(managed, 'assigned')
    reply = base.step(token=base.choose(menu, 'Invoices'))
    member.role = 'manager'
    member.save()
    assert block(reply) == 'access_or_target_changed'


@pytest.mark.parametrize('change', ['unverified', 'inactive', 'removed', 'suspended'])
def test_manager_identity_and_membership_revocation_still_deny(managed, change):
    binding = bind(managed['assigned'], base.PHONE)
    if change == 'unverified':
        managed['assigned'].account_access_state.delete()
    elif change == 'inactive':
        managed['assigned'].is_active = False
        managed['assigned'].save()
        binding.user.refresh_from_db()
    elif change == 'removed':
        managed['member'].is_active = False
        managed['member'].save()
    else:
        managed['org'].is_active = False
        managed['org'].save()
    with pytest.raises(PermissionDenied):
        actor_context(binding, managed['org'].pk)


def test_manager_cross_workspace_and_cover_expiry_are_fresh(managed):
    other = Organization.objects.create(name='Other workspace')
    ctx = context(managed)
    with pytest.raises(PermissionDenied):
        actor_context(ctx.binding, other.pk)
    teammate = get_user_model().objects.create_user(username='teammate')
    teammate_member = OrganizationMembership.objects.create(
        user=teammate, organization=managed['org'], role='manager',
    )
    PropertyAssignment.objects.create(
        organization=managed['org'], membership=teammate_member, property=managed['other_property'],
    )
    cover = CoverSession.objects.create(
        organization=managed['org'], manager=managed['member'], covering_for=teammate_member,
        expires_at=timezone.now() + timedelta(hours=1), reason='Test cover',
    )
    assert context(managed).scope(Invoice.objects.all()).count() == 2
    cover.expires_at = timezone.now() - timedelta(seconds=1)
    cover.save()
    assert context(managed).scope(Invoice.objects.all()).count() == 1


@pytest.mark.parametrize('action', ['pay_rent', 'payment_proof', 'review_proof',
                                  'reminders', 'reminder', 'reminder_confirm'])
def test_manager_money_and_reminder_actions_keep_website_handoff(managed, action):
    ctx = context(managed)
    conversation = WhatsAppConversation.objects.create(binding=ctx.binding)
    adapter = Mock()
    with patch('apps.notifications.whatsapp.conversation.MONEY_ADAPTER', adapter):
        view = run_action(ctx, conversation, action)
    assert 'Manage payments and reminders in Dwella' in view['text']
    adapter.start.assert_not_called()
    titles = [item['title'] for item in view['options']]
    assert 'Review payment proof' not in titles and 'Send rent reminder' not in titles
    assert not Payment.objects.exists()


def test_manager_list_query_count_does_not_grow_per_invoice(managed):
    ctx = context(managed)
    conversation = WhatsAppConversation.objects.create(binding=ctx.binding)
    with CaptureQueriesContext(connection) as small:
        view = run_action(ctx, conversation, 'invoices')
    assert len(view['options']) == 2  # one invoice and Main menu
    invoice = managed['invoice']
    Invoice.objects.bulk_create([
        Invoice(organization=managed['org'], tenant=invoice.tenant, unit=invoice.unit,
                reference=f'INV-EXTRA-{index}', issue_date=invoice.issue_date,
                due_date=invoice.due_date, total=1)
        for index in range(20)
    ])
    ctx = context(managed)
    with CaptureQueriesContext(connection) as full:
        view = run_action(ctx, conversation, 'invoices')
    assert len(view['options']) == 9  # bounded seven invoices, More, Main menu
    assert len(small) == len(full) <= 4
    print(f'Assigned-manager invoice listing: {len(small)} queries small; {len(full)} full')


@pytest.mark.django_db(transaction=True)
def test_manager_pdf_is_not_sent_if_assignment_removed_during_upload(managed, settings):
    settings.WHATSAPP_TYPING_ENABLED = False
    menu = base.workspace(managed, 'assigned')
    listing = base.step(token=base.choose(menu, 'Invoices'))
    detail = base.step(token=base.choose(listing, managed['invoice'].reference))
    reply = base.step(token=base.choose(detail, 'Download PDF'))
    assert reply.view['document']['kind'] == 'invoice'

    def upload(*args):
        assert not connection.in_atomic_block
        managed['assignment'].delete()
        return {'id': 'synthetic-private-media'}

    with (
        patch('apps.notifications.whatsapp.transport.post_request', side_effect=upload) as media,
        patch('apps.notifications.whatsapp.transport.post_json') as send,
    ):
        dispatch_replies()
    assert media.call_count == 1
    send.assert_not_called()
    reply.refresh_from_db()
    assert reply.status == 'cancelled'
