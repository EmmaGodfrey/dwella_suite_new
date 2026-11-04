from django.core.management.base import BaseCommand

from apps.notifications.whatsapp.media import cleanup_media, fetch_media
from apps.notifications.whatsapp.transport import dispatch_replies
from apps.notifications.whatsapp.worker import cleanup, process_inbox


class Command(BaseCommand):
    help = 'Process bounded WhatsApp conversations; closed until explicitly enabled.'

    def handle(self, *args, **options):
        processed = process_inbox()
        fetch_media()
        accepted = dispatch_replies()
        cleanup()
        cleanup_media()
        self.stdout.write(f'WhatsApp processed {processed}; accepted {accepted}.')
