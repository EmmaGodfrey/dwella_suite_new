"""Send a proof's files to the verified reviewer, just before the review message itself."""
import logging
import uuid

from django.conf import settings

from apps.billing.models import PaymentProofFile
from apps.common.provider_http import post_json, post_request

logger = logging.getLogger(__name__)
FAILED_NOTE = '\n\nThe files could not be sent here, so ask the tenant if you need to see them.'
MAX_IMAGE_BYTES = 5 * 1024 ** 2  # Meta's image limit. Larger files go as documents.


def _multipart(fields, item):
    boundary = uuid.uuid4().hex
    lines = []
    for name, value in fields.items():
        lines += [f'--{boundary}'.encode(),
                  f'Content-Disposition: form-data; name="{name}"'.encode(), b'', value.encode()]
    lines += [f'--{boundary}'.encode(),
              f'Content-Disposition: form-data; name="file"; filename="{item.public_id}"'.encode(),
              f'Content-Type: {item.content_type}'.encode(), b'', bytes(item.content),
              f'--{boundary}--'.encode(), b'']
    return b'\r\n'.join(lines), f'multipart/form-data; boundary={boundary}'


def send_evidence(reply):
    """True when every file went out. A failure never blocks the review message."""
    base = (f'https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/'
            f'{settings.WHATSAPP_PHONE_NUMBER_ID}')
    auth = {'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}'}
    items = PaymentProofFile.objects.filter(
        organization_id=reply.organization_id, public_id__in=reply.view['evidence'],
    ).order_by('created_at')[:6]
    complete = True
    for item in items:
        try:
            body, content_type = _multipart(
                {'messaging_product': 'whatsapp', 'type': item.content_type}, item,
            )
            media = post_request(f'{base}/media', body, content_type, auth)['id']
            kind = ('image' if item.content_type == 'image/jpeg' and item.size <= MAX_IMAGE_BYTES
                    else 'document')
            target = {'id': media}
            if kind == 'document':
                target['filename'] = item.name
            post_json(f'{base}/messages', {
                'messaging_product': 'whatsapp', 'to': reply.inbound.phone[1:],
                'type': kind, kind: target,
            }, auth)
        except Exception as error:
            # Logged by class only, so credentials and message content stay out of logs.
            logger.warning('WhatsApp evidence failure class=%s', type(error).__name__)
            complete = False
    return complete
