"""Best-effort native typing status. Never an authority for reply send outcomes."""
import json
import logging
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings

logger = logging.getLogger(__name__)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


opener = build_opener(NoRedirect)


def indicate(reply):
    if not settings.WHATSAPP_TYPING_ENABLED or not reply.binding_id:
        return False
    if reply.view.get('notice') == 'stop_ack':
        return False
    try:
        body = {
            'messaging_product': 'whatsapp', 'status': 'read',
            'message_id': reply.inbound.provider_id, 'typing_indicator': {'type': 'text'},
        }
        request = Request(
            f'https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/'
            f'{settings.WHATSAPP_PHONE_NUMBER_ID}/messages',
            data=json.dumps(body).encode(), method='POST',
            headers={'Content-Type': 'application/json',
                     'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}'},
        )
        with opener.open(request, timeout=0.5) as result:
            return json.loads(result.read(1024)).get('success') is True
    except Exception as error:
        # A status timeout/rejection is independent of the actual reply. Never retry
        # it, change the claim, log provider bodies, or withhold the reply for it.
        logger.debug('WhatsApp typing status unavailable class=%s', type(error).__name__)
        return False
