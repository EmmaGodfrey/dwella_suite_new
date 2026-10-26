from django.core.management.base import BaseCommand

from apps.notifications.messaging import dispatch_messages, schedule_reminders


class Command(BaseCommand):
    help = "Schedule bounded rent reminders and dispatch explicitly enabled email."

    def handle(self, *args, **options):
        scheduled = schedule_reminders()
        sent = dispatch_messages()
        self.stdout.write(f"Scheduled {scheduled}; accepted by email transport {sent}.")
