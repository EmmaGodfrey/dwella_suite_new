"""Recoverable conversation failures and a narrowly scoped opt-out acknowledgement."""
from datetime import timedelta

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.notifications.models import PhoneMessagingConsent
from apps.subscriptions.models import WorkspaceAccessPolicy
from apps.subscriptions.services import feature_state
from apps.tenants.models import Tenant

from .access import actor_context, memberships
from .models import WhatsAppBinding, WhatsAppReply

STOP_ACK = ('WhatsApp notices and account access are now off. '
            'You can reconnect from your signed-in Dwella account when you are ready.')


def eligible_memberships(user):
    linked = Tenant.objects.filter(user=user, organization_id=OuterRef('organization_id'),
                                   is_active=True)
    return memberships(user).annotate(linked=Exists(linked)).filter(
        Q(role='landlord') | Q(linked=True),
    )


def single_workspace(binding):
    rows = list(eligible_memberships(binding.user)[:2])
    if len(rows) != 1:
        return None
    try:
        return actor_context(binding, rows[0].organization_id)
    except PermissionDenied:
        return None


def workspace_options(binding, conversation, page=0):
    from .conversation import PAGE_SIZE, choice, response, website

    rows = list(eligible_memberships(binding.user)[page:page + PAGE_SIZE + 1])
    policies = {p.organization_id: p for p in WorkspaceAccessPolicy.objects.filter(
        organization_id__in=[row.organization_id for row in rows[:PAGE_SIZE]],
    )}
    visible = [row for row in rows[:PAGE_SIZE]
               if feature_state(policies.get(row.organization_id), 'whatsapp_messages')['enabled']
               and (row.role != 'tenant' or feature_state(
                   policies.get(row.organization_id), 'tenant_portal',
               )['enabled'])]
    options = [choice(conversation, str(row.organization), 'workspace', row.organization_id,
                      member=row) for row in visible]
    if len(rows) > PAGE_SIZE:
        options.append(choice(conversation, 'More workspaces', 'workspaces', page=page + PAGE_SIZE))
    text = ('Choose your workspace.' if options else
            'No workspace is available for WhatsApp right now. Open Dwella: '
            + website('settings?tab=notifications'))
    return response(text, options, {'memberships': [
        [row.pk, row.role, row.updated_at.isoformat()] for row in visible
    ]})


def recover(binding, conversation, note):
    from .conversation import menu

    conversation.choices = {}
    conversation.draft = {}
    conversation.revision += 1
    conversation.generation = binding.generation
    conversation.expires_at = timezone.now() + timedelta(minutes=10)
    ctx = None
    if conversation.organization_id:
        try:
            ctx = actor_context(binding, conversation.organization_id)
        except PermissionDenied:
            pass
    if ctx:
        conversation.role = ctx.role
        view = menu(ctx, conversation, note)
    else:
        conversation.organization = None
        conversation.role = ''
        view = workspace_options(binding, conversation)
        view['text'] = note + '\n' + view['text']
    return view


def notice_allowed(event, kind):
    return not WhatsAppReply.objects.filter(
        inbound__phone=event.phone, created_at__gte=timezone.now() - timedelta(hours=24),
        view__notice=kind,
    ).exists()


def stop_ack_valid(reply, consent):
    from apps.notifications.provider_webhooks import STOP_WORDS

    return bool(
        reply.view.get('notice') == 'stop_ack' and reply.view.get('text') == STOP_ACK
        and set(reply.view) == {'notice', 'text', 'options', 'guards'}
        and not reply.view.get('options') and not reply.view.get('guards')
        and reply.binding_generation is None and reply.binding_id is None
        and reply.organization_id is None and not reply.role
        and reply.inbound.payload.get('text', '').strip().casefold() in STOP_WORDS
        and consent and consent.revoked_at and not consent.allowed
        and not WhatsAppBinding.objects.filter(
            phone=reply.inbound.phone, revoked_at__isnull=True,
        ).exists()
    )


def queue_stop_ack(event):
    consent = PhoneMessagingConsent.objects.filter(channel='whatsapp', phone=event.phone).first()
    view = {'notice': 'stop_ack', 'text': STOP_ACK, 'options': [], 'guards': {}}
    candidate = WhatsAppReply(inbound=event, view=view)
    if not stop_ack_valid(candidate, consent) or not notice_allowed(event, 'stop_ack'):
        return
    WhatsAppReply.objects.get_or_create(inbound=event, defaults={'view': view})
