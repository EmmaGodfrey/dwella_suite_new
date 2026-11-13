"""Fetch files for a linked sender's draft, outside any row lock, and validate them."""

import hashlib
import io
import logging
import time
import uuid
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from PIL import Image
from rest_framework.exceptions import ValidationError

from apps.audit.provider_credentials import credential
from apps.billing.proofs import clean_file
from apps.common.provider_http import ProviderRejected, get_bytes, get_json
from apps.documents.files import MAX_PHOTO_BYTES, clean_image

from .models import WhatsAppBinding, WhatsAppConversation, WhatsAppMedia

logger = logging.getLogger(__name__)
ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'application/pdf'}
# The bearer token is sent to this URL, so an unexpected host is refused rather than trusted.
MEDIA_HOSTS = ('.fbsbx.com', '.fbcdn.net', '.whatsapp.net')
BACKOFF = [30, 120, 600]


def keep(binding, media_id, *, repair=False):
    return WhatsAppMedia.objects.create(
        binding=binding, binding_generation=binding.generation, media_id=media_id,
        name=f'maintenance/photos/{uuid.uuid4().hex}.jpg' if repair else '',
    )


def wanted(row):
    if row.created_at < timezone.now() - timedelta(days=2):
        return False
    binding = WhatsAppBinding.objects.select_related('user').filter(
        pk=row.binding_id, revoked_at__isnull=True, generation=row.binding_generation,
    ).first()
    if binding is None:
        return False
    if not WhatsAppMedia.objects.filter(
        pk=row.pk, status__in=['queued', 'fetching', 'ready'],
    ).exists():
        return False
    row.binding = binding
    conversation = WhatsAppConversation.objects.filter(binding=binding).first()
    if not conversation or row.pk not in conversation.draft.get('files', []):
        return False
    if row.name.startswith('maintenance/photos/'):
        from .repair_photos import wanted as repair_wanted

        return repair_wanted(row, conversation)
    return True


def download(row):
    auth = {'Authorization': f"Bearer {credential('WHATSAPP_ACCESS_TOKEN')}"}
    meta = get_json(
        f'https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/{row.media_id}', auth,
    )
    url = urlsplit(meta['url'])
    host = (url.hostname or '').casefold()
    if url.scheme != 'https' or not host.endswith(MEDIA_HOSTS):
        raise ProviderRejected('unexpected_media_host')
    if meta.get('mime_type', '').split(';')[0].strip().casefold() not in ALLOWED_TYPES:
        raise ValidationError('Unsupported file type.')
    if (row.name.startswith('maintenance/photos/') and
            meta.get('mime_type', '').split(';')[0].strip().casefold() not in
            {'image/jpeg', 'image/png', 'image/webp'}):
        raise ValidationError('Send a JPEG, PNG or WebP photo.')
    if int(meta.get('file_size') or 0) > MAX_PHOTO_BYTES:
        raise ValidationError('This file is too large.')
    raw = get_bytes(meta['url'], auth, MAX_PHOTO_BYTES)
    if meta.get('sha256') and hashlib.sha256(raw).hexdigest() != meta['sha256']:
        raise ValueError('Media digest mismatch.')
    if row.name.startswith('maintenance/photos/'):
        try:
            with Image.open(io.BytesIO(raw)) as image:
                if image.width * image.height > 40_000_000:
                    raise ValidationError('Photos must be no larger than 40 megapixels.')
        except (Image.DecompressionBombError, OSError, ValueError) as error:
            raise ValidationError('Choose a valid photo.') from error
        return clean_image(raw, photo=True), 'image/jpeg', row.name
    # The same check as the website, keeping the re-encoded copy without its metadata.
    return clean_file(SimpleUploadedFile('payment-proof', raw))


def fetch_media(limit=10, seconds=20):
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED or not credential('WHATSAPP_ACCESS_TOKEN'):
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
        claimed_at = timezone.now()
        if not WhatsAppMedia.objects.filter(pk=pk, status='queued').update(
            status='fetching', claimed_at=claimed_at, attempts=F('attempts') + 1,
        ):
            continue
        row = WhatsAppMedia.objects.select_related('binding').get(pk=pk)
        if not wanted(row):
            if row.name.startswith('maintenance/photos/'):
                default_storage.delete(row.name)
            row.delete()
            continue
        updates = {}
        try:
            content, content_type, name = download(row)
            if row.name.startswith('maintenance/photos/'):
                if not wanted(row):
                    raise ValidationError('This repair draft is no longer available.')
                if not default_storage.exists(name):
                    stored = default_storage.save(name, ContentFile(content))
                    if stored != name:
                        default_storage.delete(stored)
                        raise ValidationError('Could not store this photo.')
                content = None
            updates = {'status': 'ready', 'reason': '', 'content': content,
                       'content_type': content_type, 'name': name}
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
        updated = WhatsAppMedia.objects.filter(
            pk=pk, status='fetching', claimed_at=claimed_at,
        ).update(**updates)
        ready += bool(updated and updates['status'] == 'ready')
    return ready


def cleanup_media(limit=200):
    # A draft lasts at most a day, so anything older was abandoned and must not linger.
    with transaction.atomic():
        rows = list(WhatsAppMedia.objects.select_for_update().filter(
            created_at__lt=timezone.now() - timedelta(days=2),
        ).exclude(
            status='fetching', claimed_at__gte=timezone.now() - timedelta(minutes=2),
        ).order_by('pk').only('pk', 'name')[:min(limit, 1000)])
        # Confirmation locks these same rows. Mark them unavailable before removing
        # files outside the transaction, so cleanup cannot delete transferred photos.
        WhatsAppMedia.objects.filter(pk__in=[row.pk for row in rows]).update(
            status='rejected', reason='expired',
        )
    for row in rows:
        if row.name.startswith('maintenance/photos/'):
            default_storage.delete(row.name)
    WhatsAppMedia.objects.filter(pk__in=[row.pk for row in rows]).delete()
