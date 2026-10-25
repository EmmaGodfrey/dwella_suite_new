import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.integrations.models import FiscalReceipt
from apps.integrations.smart_invoice import resend_receipts
from apps.organizations.models import Organization

from ...services import apply_late_fees, first_of_month, generate_rent_invoices

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Issue this month's rent invoices for every workspace and add late fees "
        "that have fallen due, then resend anything ZRA Smart Invoice has not "
        "received yet. Safe to run daily; nothing is billed twice."
    )

    def handle(self, *args, **options):
        period = first_of_month(timezone.localdate())
        failed = []
        for organization in Organization.objects.filter(is_active=True):
            # One workspace's problem must not stop everyone else's billing.
            try:
                created, _ = generate_rent_invoices(organization, period)
                fees = apply_late_fees(organization)
                resent = resend_receipts(FiscalReceipt.objects.filter(organization=organization))
            except Exception:
                logger.exception("Billing failed for workspace %s", organization.pk)
                failed.append(organization.name)
                continue
            if created or fees or resent:
                self.stdout.write(
                    f"{organization.name}: {created} invoices, {fees} late fees,"
                    f" {resent} sent to ZRA"
                )
        if failed:
            # Fails the run so the scheduler records it and tries again later.
            raise CommandError(
                f"Billing failed for {len(failed)} workspace(s): {', '.join(failed)}"
            )
        self.stdout.write(self.style.SUCCESS(f"Billing run for {period:%B %Y} complete."))
