from django.core.management.base import BaseCommand

from apps.audit.runtime_settings import runtime_settings
from apps.marketing.emails import send_due_emails


class Command(BaseCommand):
    help = "Send due beta applicant emails (welcome, countdown, beta-day sign-in). Safe to rerun."

    def handle(self, *args, **options):
        if not runtime_settings()["beta_emails_enabled"]:
            self.stdout.write("Beta emails are paused in platform settings.")
            return
        sent, failed = send_due_emails()
        self.stdout.write(f"Beta emails: {sent} sent, {failed} failed.")
