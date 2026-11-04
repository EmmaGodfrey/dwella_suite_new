"""Fetch files for a linked sender's draft, outside any row lock, and validate them."""
import hashlib
import logging
import time
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.billing.proofs import clean_file
from apps.common.provider_http import ProviderRejected, get_bytes, get_json
from apps.documents.files import MAX_PHOTO_BYTES

from .models import WhatsAppConversation, WhatsAppMedia

logger = logging.getLogger(__name__)
ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'application/pdf'}
# The bearer token is sent to this URL, so an unexpected host is refused rather than trusted.
MEDIA_HOSTS = ('.fbsbx.com', '.fbcdn.net', '.whatsapp.net')
BACKOFF = [30, 120, 600]


def keep(binding, media_id):
    return WhatsAppMedia.objects.create(
        binding=binding, binding_generation=binding.generation, media_id=media_id,
    )


def wanted(row):
    binding = row.binding
    if binding.revoked_at or binding.generation != row.binding_generation:
        return False
    conversation = WhatsAppConversation.objects.filter(binding=binding).first()
    return bool(conversation and row.pk in conversation.draft.get('files', []))


def download(row):
    auth = {'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}'}
    meta = get_json(
        f'https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/{row.media_id}', auth,
    )
    url = urlsplit(meta['url'])
    host = (url.hostname or '').casefold()
    if url.scheme != 'https' or not host.endswith(MEDIA_HOSTS):
        raise ProviderRejected('unexpected_media_host')
    if meta.get('mime_type', '').split(';')[0].strip().casefold() not in ALLOWED_TYPES:
        raise ValidationError('Unsupported file type.')
    if int(meta.get('file_size') or 0) > MAX_PHOTO_BYTES:
        raise ValidationError('This file is too large.')
    raw = get_bytes(meta['url'], auth, MAX_PHOTO_BYTES)
    if meta.get('sha256') and hashlib.sha256(raw).hexdigest() != meta['sha256']:
        raise ValueError('Media digest mismatch.')
    # The same check as the website, keeping the re-encoded copy without its metadata.
    return clean_file(SimpleUploadedFile('payment-proof', raw))


def fetch_media(limit=10, seconds=20):
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED or not settings.WHATSAPP_ACCESS_TOKEN:
        return 0
    now = timezone.now()
    WhatsAppMedia.objects.filter(
        status='fetching', claimed_at__lt=now - timedelta(minutes=2),
    ).update(status='queued')
    ids = list(WhatsAppMedia.objects.filter(
        status='queued', available_at__lte=now,
    ).order_by('pk').values_list('pk', flat=True)[:min(limit, 25)])
    started, ready = time.monotonic(), 0
    for pk in ids:
        if time.monotonic() - started >= seconds:
            break
        if not WhatsAppMedia.objects.filter(pk=pk, status='queued').update(
            status='fetching', claimed_at=timezone.now(), attempts=F('attempts') + 1,
        ):
            continue
        row = WhatsAppMedia.objects.select_related('binding').get(pk=pk)
        if not wanted(row):
            row.delete()
            continue
        updates = {}
        try:
            content, content_type, name = download(row)
            updates = {'status': 'ready', 'reason': '', 'content': content,
                       'content_type': content_type, 'name': name}
            ready += 1
        except ValidationError:
            updates = {'status': 'rejected', 'reason': 'invalid_file'}
        except ProviderRejected as error:
            # Rate limits and 5xx can clear up; other refusals mean this reference will not work.
            final = not (error.code == 'http_429' or error.code.startswith('http_5'))
            updates = ({'status': 'rejected', 'reason': error.code} if final else None)
        except Exception as error:
            logger.warning('WhatsApp media failure id=%s class=%s', pk, type(error).__name__)
            updates = None
        if updates is None:
            exhausted = row.attempts >= len(BACKOFF) + 1
            updates = ({'status': 'rejected', 'reason': 'download_failed'} if exhausted else {
                'status': 'queued',
                'available_at': timezone.now() + timedelta(seconds=BACKOFF[row.attempts - 1]),
            })
        # Files are large, so only the outcome is written, never a save of the whole stale row.
        WhatsAppMedia.objects.filter(pk=pk, status='fetching').update(**updates)
    return ready


def cleanup_media(limit=200):
    # A draft lasts at most a day, so anything older was abandoned and must not linger.
    ids = list(WhatsAppMedia.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=2),
    ).order_by('pk').values_list('pk', flat=True)[:min(limit, 1000)])
    WhatsAppMedia.objects.filter(pk__in=ids).delete()
