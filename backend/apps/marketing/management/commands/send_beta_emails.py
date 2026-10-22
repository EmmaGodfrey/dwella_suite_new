from django.conf import settings
from django.core.management.base import BaseCommand

from apps.marketing.emails import send_due_emails


class Command(BaseCommand):
    help = "Send due beta applicant emails (welcome, countdown, beta-day sign-in). Safe to rerun."

    def handle(self, *args, **options):
        if not settings.BETA_EMAILS_ENABLED:
            self.stdout.write("Beta emails are off; set APP_BETA_EMAILS_ENABLED=true to send.")
            return
        sent, failed = send_due_emails()
        self.stdout.write(f"Beta emails: {sent} sent, {failed} failed.")
