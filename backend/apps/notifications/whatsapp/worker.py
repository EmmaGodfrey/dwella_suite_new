"""Short inbox transactions, separate bounded network dispatch, conservative retries."""
import logging
import time
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.notifications.models import NotificationPhoneLink
from apps.notifications.provider_webhooks import STOP_WORDS

from .access import IdentityDenied, require_binding, revoke
from .conversation import handle
from .models import WhatsAppBinding, WhatsAppConversation, WhatsAppInbound, WhatsAppReply
from .recovery import notice_allowed, queue_stop_ack, recover

logger = logging.getLogger(__name__)


def _process(pk):
    candidate = WhatsAppInbound.objects.get(pk=pk)
    with transaction.atomic():
        binding = WhatsAppBinding.objects.select_for_update(of=('self',)).select_related(
            'user',
        ).filter(phone=candidate.phone, revoked_at__isnull=True).first()
        event = WhatsAppInbound.objects.select_for_update().get(pk=pk)
        now = timezone.now()
        if event.status != 'queued' or event.available_at > now:
            return
        if event.happened_at <= now - timedelta(hours=24):
            event.status, event.reason = 'done', 'stale'
            event.save(update_fields=['status', 'reason'])
            return
        text = event.payload.get('text', '').strip().casefold()
        if text in STOP_WORDS or text == 'connect':
            if text in STOP_WORDS:
                queue_stop_ack(event)
            event.status, event.reason = 'done', 'control_message'
            event.save(update_fields=['status', 'reason'])
            return
        view = {'text': 'Connect this number from your signed-in Dwella account: '
                + settings.FRONTEND_URL.rstrip('/') + '/settings?tab=notifications',
                'options': [], 'guards': {}, 'notice': 'connect'}
        conversation = None
        identity_notice = False
        if binding:
            try:
                require_binding(binding)
                if event.binding_generation != binding.generation:
                    event.status, event.reason = 'done', 'old_binding_event'
                    event.save(update_fields=['status', 'reason'])
                    return
                conversation, _ = WhatsAppConversation.objects.select_for_update().get_or_create(
                    binding=binding, defaults={'generation': binding.generation},
                )
                if (conversation.last_event_at and
                        event.happened_at < conversation.last_event_at):
                    event.status, event.reason = 'done', 'out_of_order'
                    event.save(update_fields=['status', 'reason'])
                    return
                # A failed domain action must roll back its partial work as well as the draft.
                with transaction.atomic():
                    view = handle(binding, conversation, event)
                    conversation.last_event_at = event.happened_at
                    conversation.save()
            except IdentityDenied:
                revoke(user=binding.user)
                binding = None
                conversation = None
                identity_notice = True
                view = {'text': 'Your connection or access changed. Reconnect WhatsApp in '
                        'Dwella settings.', 'options': [], 'guards': {}, 'notice': 'reconnect'}
            except PermissionDenied:
                conversation.refresh_from_db()
                view = recover(binding, conversation,
                               'That record or workspace is no longer available. '
                               'Choose another option or open Dwella.')
                conversation.last_event_at = event.happened_at
                conversation.save()
            except ValidationError:
                conversation.refresh_from_db()
                view = recover(binding, conversation,
                               'That request could not be completed. Choose an option again.')
                conversation.save()
        # Per-number admission prevents webhook-driven unbounded auto-replies.
        history = WhatsAppReply.objects.filter(
            inbound__phone=event.phone, created_at__gte=now - timedelta(hours=24),
        )
        if identity_notice:
            permitted = notice_allowed(event, 'reconnect')
        elif binding:
            permitted = history.count() < 60
        else:
            permitted = not history.filter(binding__isnull=True, view__notice='connect').exists()
        if not permitted:
            event.status, event.reason = 'done', 'daily_reply_limit'
        else:
            WhatsAppReply.objects.get_or_create(inbound=event, defaults={
                'binding': binding, 'binding_generation': binding.generation if binding else None,
                'conversation_revision': conversation.revision if conversation else 0,
                'organization_id': conversation.organization_id if conversation else None,
                'role': conversation.role if conversation else '', 'view': view,
            })
            event.status = 'done'
        event.attempts += 1
        event.save(update_fields=['status', 'reason', 'attempts'])


def process_inbox(limit=50, seconds=20, *, ordered=False):
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED:
        return 0
    started, count = time.monotonic(), 0
    queue = WhatsAppInbound.objects.filter(
        status='queued', available_at__lte=timezone.now(),
    )
    if ordered:
        earlier = WhatsAppInbound.objects.filter(phone=OuterRef('phone'), status='queued').filter(
            Q(happened_at__lt=OuterRef('happened_at'))
            | Q(happened_at=OuterRef('happened_at'), pk__lt=OuterRef('pk')),
        )
        pending = WhatsAppReply.objects.filter(
            inbound__phone=OuterRef('phone'), status__in=['queued', 'sending'],
        )
        queue = queue.alias(earlier=Exists(earlier), pending=Exists(pending)).filter(
            earlier=False, pending=False,
        )
    ids = list(queue.order_by('happened_at', 'pk').values_list('pk', flat=True)[:min(limit, 100)])
    for pk in ids:
        if time.monotonic() - started >= seconds:
            break
        try:
            _process(pk)
            count += 1
        except Exception as error:
            # Log class and identity only, never message content/exception values.
            logger.warning('WhatsApp inbox failure id=%s class=%s', pk, type(error).__name__)
            with transaction.atomic():
                row = WhatsAppInbound.objects.select_for_update().get(pk=pk)
                if row.status != 'queued':
                    continue
                row.attempts += 1
                row.status = 'failed' if row.attempts >= 4 else 'queued'
                row.reason = 'processing_error'
                row.available_at = timezone.now() + timedelta(
                    seconds=[30, 120, 600, 600][min(row.attempts - 1, 3)],
                )
                row.save(update_fields=['attempts', 'status', 'reason', 'available_at'])
    return count


def cleanup(limit=200):
    now = timezone.now()
    size = min(limit, 1000)
    # Payload expiry is independent of processing state; old tombstones still dedupe retries.
    ids = list(WhatsAppInbound.objects.filter(received_at__lt=now - timedelta(days=30)).exclude(
        payload={},
    ).order_by('pk').values_list('pk', flat=True)[:size])
    WhatsAppInbound.objects.filter(pk__in=ids).update(payload={}, status='done', reason='expired')
    ids = list(WhatsAppReply.objects.filter(created_at__lt=now - timedelta(days=90)).exclude(
        status='sending',
    ).order_by('pk').values_list('pk', flat=True)[:size])
    WhatsAppReply.objects.filter(pk__in=ids).delete()
    ids = list(WhatsAppInbound.objects.filter(
        received_at__lt=now - timedelta(days=90), whatsappreply__isnull=True,
    ).order_by('pk').values_list('pk', flat=True)[:size])
    WhatsAppInbound.objects.filter(pk__in=ids).delete()
    ids = list(WhatsAppConversation.objects.filter(
        expires_at__lt=now - timedelta(days=7),
    ).filter(~Q(draft={}) | ~Q(choices={})).values_list('pk', flat=True)[:size])
    WhatsAppConversation.objects.filter(pk__in=ids).update(draft={}, choices={})
    ids = list(NotificationPhoneLink.objects.filter(
        expires_at__lt=now - timedelta(days=7),
    ).values_list('pk', flat=True)[:size])
    NotificationPhoneLink.objects.filter(pk__in=ids).delete()
