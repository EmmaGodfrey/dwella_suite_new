from django.core.management.base import BaseCommand

from apps.notifications.whatsapp.media import cleanup_media, fetch_media
from apps.notifications.whatsapp.notices import cleanup_notices, dispatch_proof_notices
from apps.notifications.whatsapp.transport import dispatch_replies
from apps.notifications.whatsapp.worker import cleanup, process_inbox


class Command(BaseCommand):
    help = 'Process bounded WhatsApp conversations; closed until explicitly enabled.'

    def handle(self, *args, **options):
        processed = process_inbox()
        fetch_media()
        accepted = dispatch_replies()
        accepted += dispatch_proof_notices()
        cleanup()
        cleanup_media()
        cleanup_notices()
        self.stdout.write(f'WhatsApp processed {processed}; accepted {accepted}.')
