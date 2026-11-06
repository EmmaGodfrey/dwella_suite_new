from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.notifications.models import NotificationPhoneLink, OperationalDelivery
from apps.notifications.operational import dispatch_operational, schedule_operational


class Command(BaseCommand):
    help = "Queue required operational notices and dispatch bounded outbox work."

    def handle(self, *args, **options):
        # Alpha users exercise fresh, explicit events without sweeping historical
        # tenancy records into newly unrestricted email/phone destinations.
        scheduled = 0 if settings.ALPHA_TEST_ENABLED else schedule_operational()
        sent = dispatch_operational()
        # Operational metadata only. Invoices, payments and signing evidence are retained.
        old = list(OperationalDelivery.objects.filter(
            status__in=["sent", "cancelled", "failed", "held", "review"],
            created_at__lt=timezone.now() - timedelta(days=90),
        ).order_by("pk").values_list("pk", flat=True)[:500])
        OperationalDelivery.objects.filter(pk__in=old).delete()
        links = list(NotificationPhoneLink.objects.filter(
            expires_at__lt=timezone.now() - timedelta(days=7),
        ).order_by("pk").values_list("pk", flat=True)[:500])
        NotificationPhoneLink.objects.filter(pk__in=links).delete()
        self.stdout.write(f"Operational scheduled {scheduled}; transport accepted {sent}.")
