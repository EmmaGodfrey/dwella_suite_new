"""User-initiated replies only. Claims commit before bounded provider I/O."""
import time
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.common.provider_http import ProviderRejected, post_json
from apps.notifications.models import PhoneMessagingConsent
from apps.notifications.phone_messaging import normalize_phone, phone_allowed, whatsapp_ready

from .access import actor_context, auth_stamp, memberships, require_actor
from .conversation import guards_current
from .models import WhatsAppBinding, WhatsAppConversation, WhatsAppReply


def block(reply):
    now = timezone.now()
    if reply.binding_generation is not None and reply.binding_id is None:
        return 'binding_removed'
    if reply.role and reply.organization_id is None:
        return 'workspace_removed'
    if reply.created_at < now - timedelta(minutes=10):
        return 'reply_expired'
    if reply.inbound.number_id != settings.WHATSAPP_PHONE_NUMBER_ID:
        return 'number_changed'
    if not phone_allowed(reply.inbound.phone):
        return 'recipient_restricted'
    consent = PhoneMessagingConsent.objects.filter(
        channel='whatsapp', phone=reply.inbound.phone,
    ).first()
    if not consent or consent.revoked_at:
        return 'recipient_opted_out'
    if not consent.last_inbound_at or consent.last_inbound_at <= now - timedelta(hours=24):
        return 'reply_window_closed'
    if reply.binding_id:
        binding = WhatsAppBinding.objects.select_related('user').get(pk=reply.binding_id)
        if (binding.revoked_at or binding.phone != reply.inbound.phone or
                binding.generation != reply.binding_generation or
                binding.auth_stamp != auth_stamp(binding.user)):
            return 'binding_changed'
        require_actor(binding.user)
        conversation = WhatsAppConversation.objects.filter(binding=binding).first()
        if (not conversation or conversation.revision != reply.conversation_revision or
                conversation.generation != binding.generation or conversation.expires_at <= now):
            return 'conversation_changed'
        if reply.organization_id:
            ctx = actor_context(binding, reply.organization_id)
            if ctx.role != reply.role or not guards_current(ctx, reply.view.get('guards', {})):
                return 'access_or_target_changed'
        elif 'memberships' in reply.view.get('guards', {}):
            expected = reply.view['guards']['memberships']
            actual = [[r.pk, r.role, r.updated_at.isoformat()] for r in
                      memberships(binding.user).filter(pk__in=[r[0] for r in expected])]
            if sorted(actual) != sorted(expected):
                return 'membership_changed'
    elif WhatsAppBinding.objects.filter(
        phone=reply.inbound.phone, revoked_at__isnull=True,
    ).exists():
        return 'binding_changed'
    return ''


def payload(reply):
    view = reply.view
    result = {'messaging_product': 'whatsapp', 'to': reply.inbound.phone[1:],
              'biz_opaque_callback_data': str(reply.public_id)}
    options = view.get('options', [])
    if not options:
        return {**result, 'type': 'text', 'text': {'body': view['text']}}
    if len(options) <= 3 and all(len(row['title']) <= 20 for row in options):
        interactive = {'type': 'button', 'body': {'text': view['text']}, 'action': {
            'buttons': [{'type': 'reply', 'reply': row} for row in options],
        }}
    else:
        interactive = {'type': 'list', 'body': {'text': view['text']}, 'action': {
            'button': 'Choose an option', 'sections': [{'rows': options[:10]}],
        }}
    return {**result, 'type': 'interactive', 'interactive': interactive}


def dispatch_replies(limit=20, seconds=30):
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED or not whatsapp_ready():
        return 0
    now = timezone.now()
    # A process dying during network I/O leaves an uncertain outcome; never resend it.
    WhatsAppReply.objects.filter(
        status='sending', claimed_at__lt=now - timedelta(minutes=2),
    ).update(
        status='review', reason='send_outcome_unknown',
    )
    ids = list(WhatsAppReply.objects.filter(status='queued').order_by('pk').values_list(
        'pk', flat=True,
    )[:min(limit, 50)])
    started, accepted = time.monotonic(), 0
    for pk in ids:
        if time.monotonic() - started >= seconds:
            break
        token = uuid.uuid4()
        with transaction.atomic():
            reply = WhatsAppReply.objects.select_for_update(of=('self',)).select_related(
                'inbound',
            ).get(pk=pk)
            if reply.status != 'queued':
                continue
            try:
                reason = block(reply)
            except APIException:
                reason = 'access_denied'
            if reason:
                reply.status, reply.reason = 'cancelled', reason
                reply.save(update_fields=['status', 'reason'])
                continue
            reply.status, reply.claim_token, reply.claimed_at = 'sending', token, timezone.now()
            reply.save(update_fields=['status', 'claim_token', 'claimed_at'])
        # STOP or membership removal can happen after claiming; check again immediately
        # before I/O without keeping a row lock across the remote request.
        try:
            reason = block(reply)
            if reason:
                WhatsAppReply.objects.filter(pk=pk, claim_token=token, status='sending').update(
                    status='cancelled', reason=reason,
                )
                continue
            result = post_json(
                f'https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/'
                f'{settings.WHATSAPP_PHONE_NUMBER_ID}/messages', payload(reply),
                {'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}'},
            )
            provider_id = result['messages'][0]['id']
            if not isinstance(provider_id, str) or not provider_id or len(provider_id) > 160:
                raise ValueError('Invalid provider response.')
        except APIException:
            WhatsAppReply.objects.filter(pk=pk, claim_token=token, status='sending').update(
                status='cancelled', reason='access_denied',
            )
        except ProviderRejected as error:
            # The shared transport only exposes HTTP codes, so 5xx is not proof of rejection.
            uncertain = error.code.startswith('http_5')
            WhatsAppReply.objects.filter(pk=pk, claim_token=token, status='sending').update(
                status='review' if uncertain else 'failed',
                reason='send_outcome_unknown' if uncertain else error.code,
            )
        except Exception:
            WhatsAppReply.objects.filter(pk=pk, claim_token=token, status='sending').update(
                status='review', reason='send_outcome_unknown',
            )
        else:
            WhatsAppReply.objects.filter(pk=pk, claim_token=token, status='sending').update(
                status='sent', provider_id=provider_id,
            )
            # A correlated callback may already have advanced to delivered/read/failed.
            WhatsAppReply.objects.filter(pk=pk, claim_token=token, provider_id='').update(
                provider_id=provider_id,
            )
            accepted += 1
    return accepted


def apply_reply_status(data, stamp):
    reference = data.get('biz_opaque_callback_data')
    query = Q(provider_id=data['id'])
    if reference:
        try:
            query |= Q(public_id=uuid.UUID(reference), status__in=['sending', 'review'])
        except (ValueError, TypeError, AttributeError):
            return
    row = WhatsAppReply.objects.select_for_update().select_related('inbound').filter(query).first()
    if not row or normalize_phone('+' + str(data.get('recipient_id', ''))) != row.inbound.phone:
        return
    ranks = {'sending': 0, 'review': 0, 'sent': 1, 'failed': 2, 'delivered': 3, 'read': 4}
    status = data['status']
    if ranks.get(status, -1) < ranks.get(row.status, 99):
        return
    if row.provider_updated_at and stamp < row.provider_updated_at:
        return
    row.status, row.provider_id, row.provider_updated_at = status, data['id'], stamp
    row.save(update_fields=['status', 'provider_id', 'provider_updated_at'])
