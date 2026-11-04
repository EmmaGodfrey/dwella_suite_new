"""Minimal, bounded webhook capture. No network I/O or domain writes here."""
import hashlib
import json
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import WhatsAppBinding, WhatsAppInbound


def capture(message, phone, stamp):
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED:
        return
    provider_id = message.get('id')
    if not isinstance(provider_id, str) or not provider_id or len(provider_id) > 160:
        raise ValueError('Invalid message identity.')
    kind = message.get('type')
    payload = {'type': kind}
    if kind == 'text':
        text = message['text']['body']
        if not isinstance(text, str) or len(text) > 2000:
            raise ValueError('Invalid message text.')
        # Pairing challenges must not enter the retained inbox payload.
        payload['text'] = 'connect' if text.strip().casefold().startswith('connect ') else text
    elif kind == 'interactive':
        value = message['interactive']
        mode = value.get('type')
        if mode not in {'button_reply', 'list_reply'}:
            raise ValueError('Unsupported interaction.')
        token = value[mode]['id']
        if not isinstance(token, str) or len(token) > 512:
            raise ValueError('Invalid interaction identity.')
        payload.update(type='choice', token=token)
    elif kind == 'button':
        token = message['button']['payload']
        if not isinstance(token, str) or len(token) > 512:
            raise ValueError('Invalid button identity.')
        payload.update(type='choice', token=token)
    elif kind in {'image', 'document'}:
        # Only the reference is kept here. Nothing is downloaded unless a linked sender's
        # guided draft asks for it, so unknown senders' files are never fetched.
        media_id = message[kind]['id']
        if not isinstance(media_id, str) or not media_id or len(media_id) > 160:
            raise ValueError('Invalid media identity.')
        payload = {'type': 'attachment', 'media_id': media_id}
    else:
        payload = {'type': 'unsupported'}
    binding = WhatsAppBinding.objects.filter(phone=phone, revoked_at__isnull=True).first()
    if WhatsAppInbound.objects.filter(
        phone=phone, received_at__gte=timezone.now() - timedelta(hours=24),
    ).count() >= 120:
        return
    stale = stamp < timezone.now() - timedelta(hours=24)
    WhatsAppInbound.objects.get_or_create(
        number_id=settings.WHATSAPP_PHONE_NUMBER_ID, provider_id=provider_id,
        defaults={'phone': phone, 'happened_at': stamp, 'payload': payload,
                  'binding_generation': binding.generation if binding else None,
                  'status': 'done' if stale else 'queued', 'reason': 'stale' if stale else ''},
    )


def quarantine(message):
    """Keep a dedupe tombstone and reason, never a malformed body."""
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED:
        return
    identity = message.get('id') if isinstance(message, dict) else None
    if not isinstance(identity, str) or not identity or len(identity) > 160:
        identity = 'invalid:' + hashlib.sha256(
            json.dumps(message, sort_keys=True).encode()
        ).hexdigest()
    WhatsAppInbound.objects.get_or_create(
        number_id=settings.WHATSAPP_PHONE_NUMBER_ID, provider_id=identity,
        defaults={'phone': '', 'happened_at': timezone.now(), 'payload': {},
                  'status': 'quarantined', 'reason': 'malformed_event'},
    )
