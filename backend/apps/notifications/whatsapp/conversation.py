"""Small deterministic menus. No free-text command may directly mutate money."""
import hashlib
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, F, Sum
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.models import AuditEvent
from apps.billing.models import Invoice, Payment
from apps.leases.models import Lease
from apps.maintenance.models import MaintenanceRequest
from apps.maintenance.services import create_request

from .access import actor_context, memberships

PAGE_SIZE = 7
MONEY_INTENTS = {'create_invoice', 'pay_rent', 'payment_proof', 'review_proof'}
# Claude's adapter must implement this fixed interface; user text cannot import modules.
MONEY_ADAPTER = None


def register_money_adapter(adapter):
    global MONEY_ADAPTER
    if MONEY_ADAPTER is not None and MONEY_ADAPTER is not adapter:
        raise RuntimeError('A WhatsApp money adapter is already registered.')
    MONEY_ADAPTER = adapter


def fingerprint(token):
    return hashlib.sha256(token.encode()).hexdigest()


def choice(conversation, title, action, target='', page=0, member=None):
    token = secrets.token_urlsafe(24)
    conversation.choices[fingerprint(token)] = {
        'action': action, 'target': str(target), 'page': page,
        'member': member.pk if member else None,
        'membership_updated': member.updated_at.isoformat() if member else None,
    }
    return {'id': token, 'title': title[:24]}


def response(text, options=None, guards=None):
    if options and len(text) > 1024:
        raise ValidationError('This response is too long for a WhatsApp menu.')
    return {'text': text[:3500], 'options': options or [], 'guards': guards or {}}


def invoice_snapshot(query):
    return [[str(r.public_id), r.status, str(r.total), str(r.amount_paid)] for r in query]


def balance_snapshot(ctx):
    data = ctx.scope(Invoice.objects.all()).filter(status__in=Invoice.UNPAID_STATUSES).aggregate(
        count=Count('id'), balance=Sum(F('total') - F('amount_paid')),
    )
    return {'count': data['count'], 'balance': format(data['balance'] or Decimal('0'), '.2f')}


def guards_current(ctx, guards):
    if 'balance' in guards and balance_snapshot(ctx) != guards['balance']:
        return False
    if 'invoices' in guards:
        expected = guards['invoices']
        actual = invoice_snapshot(ctx.scope(Invoice.objects.all()).filter(
            public_id__in=[r[0] for r in expected],
        ).order_by('public_id'))
        if sorted(actual) != sorted(expected):
            return False
    if 'repairs' in guards:
        expected = guards['repairs']
        actual = [[str(row.public_id), row.status, row.updated_at.isoformat()] for row in
                  ctx.scope(MaintenanceRequest.objects.all()).filter(
                      public_id__in=[r[0] for r in expected],
                  )]
        if sorted(actual) != sorted(expected):
            return False
    if 'payments' in guards:
        expected = guards['payments']
        actual = [[str(row.public_id), str(row.amount), row.reversed_at is not None] for row in
                  ctx.scope(Payment.objects.all()).filter(public_id__in=[r[0] for r in expected])]
        if sorted(actual) != sorted(expected):
            return False
    return True


def website(path):
    return settings.FRONTEND_URL.rstrip('/') + '/' + path.lstrip('/')


def workspace_menu(binding, conversation, page=0):
    rows = list(memberships(binding.user)[page:page + PAGE_SIZE + 1])
    options = [choice(conversation, str(row.organization), 'workspace', row.organization_id,
                      member=row) for row in rows[:PAGE_SIZE]]
    if len(rows) > PAGE_SIZE:
        options.append(choice(conversation, 'More workspaces', 'workspaces', page=page + PAGE_SIZE))
    return response('Choose your workspace.', options, {'memberships': [
        [row.pk, row.role, row.updated_at.isoformat()] for row in rows[:PAGE_SIZE]
    ]})


def menu(ctx, conversation, note=''):
    entries = ([('What do I owe?', 'balance'), ('My invoices', 'invoices'),
                ('My receipts', 'receipts'), ('Pay rent', 'pay_rent'),
                ("I have already paid", 'payment_proof'), ('My repairs', 'repairs'),
                ('Report a repair', 'report_repair')]
               if ctx.role == 'tenant' else
               [('Who owes me?', 'balance'), ('Invoices', 'invoices'), ('Receipts', 'receipts'),
                ('Create invoice', 'create_invoice'), ('Review payment proof', 'review_proof'),
                ('Repairs', 'repairs')])
    options = [choice(conversation, title, action, member=ctx.membership)
               for title, action in entries]
    options.append(choice(conversation, 'Switch workspace', 'workspaces'))
    return response(f'{ctx.organization}\n{note or "How can Dwella help?"}', options)


def listing(ctx, conversation, action, page):
    if action == 'invoices':
        query = ctx.scope(Invoice.objects.all()).exclude(status='void').select_related('tenant')
        rows = list(query.order_by('-issue_date', '-pk')[page:page + PAGE_SIZE + 1])
        options = [choice(conversation, row.reference, 'invoice', row.public_id,
                          member=ctx.membership) for row in rows[:PAGE_SIZE]]
        text = 'Choose an invoice. Documents open securely in Dwella.'
        guards = {'invoices': invoice_snapshot(rows[:PAGE_SIZE])}
    elif action == 'receipts':
        query = ctx.scope(Payment.objects.all()).filter(reversed_at__isnull=True)
        rows = list(query.order_by('-paid_on', '-pk')[page:page + PAGE_SIZE + 1])
        options = [choice(conversation, row.receipt_number, 'receipt', row.public_id,
                          member=ctx.membership) for row in rows[:PAGE_SIZE]]
        text, guards = 'Choose a receipt.', {
            'payments': [[str(row.public_id), str(row.amount), False] for row in rows[:PAGE_SIZE]],
        }
    else:
        query = ctx.scope(MaintenanceRequest.objects.all()).filter(
            status__in=MaintenanceRequest.OPEN_STATUSES,
        )
        rows = list(query.order_by('-created_at', '-pk')[page:page + PAGE_SIZE + 1])
        options = [choice(conversation, row.reference, 'repair', row.public_id,
                          member=ctx.membership) for row in rows[:PAGE_SIZE]]
        text, guards = 'Choose an open repair.', {
            'repairs': [[str(r.public_id), r.status, r.updated_at.isoformat()]
                        for r in rows[:PAGE_SIZE]],
        }
    if not rows:
        text = 'There are no records to show here.'
    if len(rows) > PAGE_SIZE:
        options.append(choice(conversation, 'More', action, page=page + PAGE_SIZE,
                              member=ctx.membership))
    options.append(choice(conversation, 'Main menu', 'menu', member=ctx.membership))
    return response(text, options, guards)


def run_action(ctx, conversation, action, target='', page=0):
    if action in MONEY_INTENTS:
        allowed = ({'pay_rent', 'payment_proof'} if ctx.role == 'tenant' else
                   {'create_invoice', 'review_proof'})
        if action not in allowed:
            raise PermissionDenied('This action is not available for this account.')
        if MONEY_ADAPTER is None:
            return menu(ctx, conversation, 'Use Dwella for payment actions while WhatsApp '
                        'payment setup is being completed. ' + website(
                            'billing',
                        ))
        return MONEY_ADAPTER.start(ctx, conversation, action, target)
    if action == 'menu':
        conversation.draft = {}
        return menu(ctx, conversation)
    if action == 'balance':
        snapshot = balance_snapshot(ctx)
        caption = 'Your open invoices' if ctx.role == 'tenant' else 'Workspace open invoices'
        return response(f'{ctx.organization}\n{caption}: {snapshot["count"]}\n'
                        f'Outstanding: {ctx.organization.currency} '
                        f'{Decimal(snapshot["balance"]):,.2f}', [
                            choice(conversation, 'View invoices', 'invoices',
                                   member=ctx.membership),
                            choice(conversation, 'Main menu', 'menu', member=ctx.membership),
                        ], {'balance': snapshot})
    if action in {'invoices', 'receipts', 'repairs'}:
        return listing(ctx, conversation, action, page)
    if action == 'invoice':
        row = ctx.scope(Invoice.objects.all()).exclude(status='void').filter(
            public_id=target,
        ).first()
        if not row:
            raise PermissionDenied('This invoice is no longer available.')
        path = f'billing/invoices/{row.public_id}'
        return response(f'{row.reference}\nTotal: {ctx.organization.currency} {row.total:,.2f}'
                        f'\nBalance: {ctx.organization.currency} {row.balance:,.2f}'
                        f'\nDue: {row.due_date:%d %b %Y}\nOpen securely in Dwella: '
                        + website(path), guards={'invoices': invoice_snapshot([row])})
    if action == 'receipt':
        row = ctx.scope(Payment.objects.all()).filter(
            public_id=target, reversed_at__isnull=True,
        ).first()
        if not row:
            raise PermissionDenied('This receipt is no longer available.')
        path = f'billing/receipts/{row.public_id}'
        return response(f'{row.receipt_number}\n{ctx.organization.currency} {row.amount:,.2f}'
                        f'\nPaid: {row.paid_on:%d %b %Y}\nOpen securely in Dwella: '
                        + website(path), guards={
                            'payments': [[str(row.public_id), str(row.amount), False]],
                        })
    if action == 'repair':
        row = ctx.scope(MaintenanceRequest.objects.all()).filter(public_id=target).first()
        if not row:
            raise PermissionDenied('This repair is no longer available.')
        # No internal comments, vendor contacts or financial notes enter WhatsApp.
        return response(f'{row.reference}: {row.title}\nStatus: {row.get_status_display()}',
                        guards={'repairs': [[str(row.public_id), row.status,
                                             row.updated_at.isoformat()]]})
    if action == 'report_repair' and ctx.role == 'tenant':
        rows = list(Lease.objects.filter(
            organization=ctx.organization, tenant_id__in=ctx.tenant_ids, is_active=True,
            status__in=['pending_signature', 'active'],
        ).select_related('unit__property').order_by('pk')[:PAGE_SIZE + 1])
        if len(rows) > PAGE_SIZE:
            return response('Please choose your tenancy and report the repair in Dwella: '
                            + website('maintenance'))
        return response('Which home needs a repair?', [choice(
            conversation, str(row.unit), 'repair_home', row.public_id, member=ctx.membership,
        ) for row in rows])
    if action == 'repair_home' and ctx.role == 'tenant':
        lease = _repair_lease(ctx, target)
        conversation.draft = {'intent': 'repair', 'step': 'title', 'lease': str(lease.public_id)}
        return response('Describe the repair in a short title (up to 160 characters). '
                        'Send BACK to discard this draft.')
    if action in {'repair_allow_entry', 'repair_no_entry'} and ctx.role == 'tenant':
        draft = conversation.draft
        if draft.get('step') != 'entry':
            raise ValidationError('Start this repair again from the menu.')
        _repair_lease(ctx, draft['lease'])
        draft.update(step='confirm', permission_to_enter=action == 'repair_allow_entry')
        return response(f'Report repair: {draft["title"]}\n{draft["description"]}\n'
                        f'Permission to enter: {"Yes" if draft["permission_to_enter"] else "No"}'
                        '\nPhotos can be added securely in Dwella after submission.', [
                            choice(conversation, 'Confirm repair', 'repair_confirm',
                                   member=ctx.membership),
                            choice(conversation, 'Cancel', 'menu', member=ctx.membership),
                        ])
    if action == 'repair_confirm' and ctx.role == 'tenant':
        draft = conversation.draft
        if draft.get('step') != 'confirm':
            raise ValidationError('Start this repair again from the menu.')
        lease = _repair_lease(ctx, draft['lease'])
        job = create_request(
            organization=ctx.organization, reported_by=ctx.user, property=lease.unit.property,
            unit=lease.unit, tenant=lease.tenant, source='tenant', title=draft['title'],
            description=draft['description'], permission_to_enter=draft['permission_to_enter'],
        )
        AuditEvent.objects.create(actor=ctx.user, organization=ctx.organization,
                                  action='maintenance.tenant_reported',
                                  resource_type='maintenance.maintenancerequest',
                                  resource_id=str(job.public_id), metadata={'channel': 'whatsapp'})
        conversation.draft = {}
        return response(f'Repair {job.reference} submitted. Add photos or follow its progress '
                        'in Dwella: ' + website('maintenance'))
    raise ValidationError('Choose a current option from the menu.')


def _repair_lease(ctx, reference):
    lease = Lease.objects.filter(
        organization=ctx.organization, tenant_id__in=ctx.tenant_ids, public_id=reference,
        is_active=True, status__in=['active', 'pending_signature'],
    ).select_related('unit__property', 'tenant').first()
    if not lease:
        raise PermissionDenied('This tenancy is no longer available.')
    return lease


def handle(binding, conversation, inbound):
    now = timezone.now()
    payload = inbound.payload
    if conversation.expires_at <= now or conversation.generation != binding.generation:
        conversation.organization = None
        conversation.role = ''
        conversation.draft = {}
        conversation.choices = {}
        conversation.generation = binding.generation
    selected = None
    if payload.get('type') == 'choice':
        selected = conversation.choices.get(fingerprint(payload.get('token', '')))
        if not selected:
            return _reset(binding, conversation,
                          'That option expired. Choose your workspace again.')
    conversation.choices = {}
    conversation.revision += 1
    conversation.expires_at = now + timedelta(minutes=10)
    text = payload.get('text', '').strip()
    lower = text.casefold()
    if lower in {'cancel', 'back', 'menu', 'hi', 'hello', 'start', 'help'}:
        conversation.draft = {}
    if selected and selected['action'] == 'workspace':
        ctx = actor_context(binding, selected['target'])
        if (ctx.membership.pk != selected['member'] or
                ctx.membership.updated_at.isoformat() != selected['membership_updated']):
            raise PermissionDenied('Your workspace access changed. Reconnect in Dwella.')
        conversation.organization = ctx.organization
        conversation.role = ctx.role
        return menu(ctx, conversation)
    if lower == 'workspace' or (selected and selected['action'] == 'workspaces'):
        conversation.organization = None
        conversation.role = ''
        conversation.draft = {}
        return workspace_menu(binding, conversation, selected['page'] if selected else 0)
    if not conversation.organization_id:
        return workspace_menu(binding, conversation)
    ctx = actor_context(binding, conversation.organization_id)
    if ctx.role != conversation.role:
        raise PermissionDenied('Your workspace role changed. Reconnect in Dwella.')
    if selected:
        if (selected['member'] != ctx.membership.pk or
                selected['membership_updated'] != ctx.membership.updated_at.isoformat()):
            raise PermissionDenied('Your workspace access changed. Reconnect in Dwella.')
        if (conversation.draft.get('intent') in MONEY_INTENTS and MONEY_ADAPTER is not None
                and selected['action'] != 'menu'):
            return MONEY_ADAPTER.handle(ctx, conversation, payload, selected)
        return run_action(ctx, conversation, selected['action'], selected['target'],
                          selected['page'])
    if conversation.draft.get('intent') in MONEY_INTENTS and MONEY_ADAPTER is not None:
        return MONEY_ADAPTER.handle(ctx, conversation, payload, None)
    if conversation.draft.get('intent') == 'repair':
        draft = conversation.draft
        _repair_lease(ctx, draft['lease'])
        if payload.get('type') == 'attachment':
            return response('Please upload photos securely in Dwella. Continue by typing '
                            'the repair details here, or send BACK.')
        if draft['step'] == 'title':
            if not text or len(text) > 160:
                return response('Enter a title between 1 and 160 characters.')
            draft.update(title=text, step='description')
            return response('Describe the problem (up to 700 characters).')
        if draft['step'] == 'description':
            if not text or len(text) > 700:
                return response('Enter details between 1 and 700 characters.')
            draft.update(description=text, step='entry')
            return response('May the property manager enter to carry out this repair?', [
                choice(conversation, 'Entry allowed', 'repair_allow_entry', member=ctx.membership),
                choice(conversation, 'Contact me first', 'repair_no_entry', member=ctx.membership),
            ])
        return response('Choose a button from the latest repair message, or send BACK.')
    aliases = {'balance': 'balance', 'what do i owe': 'balance', 'who owes me': 'balance',
               'invoices': 'invoices', 'receipts': 'receipts', 'repairs': 'repairs',
               'pop': 'payment_proof', "i've paid": 'payment_proof', 'pay rent': 'pay_rent'}
    if lower in aliases:
        return run_action(ctx, conversation, aliases[lower])
    return menu(ctx, conversation, '' if lower in {'menu', 'hi', 'hello', 'help', 'back',
                                                  'cancel', 'start'} else
                'Choose an option below. For attachments or detailed account changes, use Dwella.')


def _reset(binding, conversation, note):
    conversation.organization = None
    conversation.role = ''
    conversation.draft = {}
    conversation.choices = {}
    conversation.revision += 1
    conversation.expires_at = timezone.now() + timedelta(minutes=10)
    view = workspace_menu(binding, conversation)
    view['text'] = note + '\n' + view['text']
    return view
