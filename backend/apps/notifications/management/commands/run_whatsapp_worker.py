import signal
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

from django.core.management.base import BaseCommand

from apps.notifications.whatsapp.responsive import run_lane
from apps.notifications.whatsapp.wakeup import LANES


class Command(BaseCommand):
    help = 'Responsive WhatsApp lanes. Idle until APP_WHATSAPP_WORKER_ENABLED is enabled.'

    def handle(self, *args, **options):
        stopping = threading.Event()
        signal.signal(signal.SIGTERM, lambda *_: stopping.set())
        signal.signal(signal.SIGINT, lambda *_: stopping.set())
        self.stdout.write('WhatsApp worker started; three bounded lanes.')
        with ThreadPoolExecutor(max_workers=len(LANES), thread_name_prefix='whatsapp') as pool:
            futures = [pool.submit(run_lane, lane, stopping) for lane in LANES]
            try:
                completed, _ = wait(futures, return_when=FIRST_COMPLETED)
                for future in completed:
                    future.result()
            finally:
                stopping.set()
