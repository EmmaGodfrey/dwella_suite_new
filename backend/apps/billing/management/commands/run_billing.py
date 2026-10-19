from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.organizations.models import Organization

from ...services import apply_late_fees, first_of_month, generate_rent_invoices


class Command(BaseCommand):
    help = (
        "Issue this month's rent invoices for every workspace and add late fees "
        "that have fallen due. Safe to run daily; nothing is billed twice."
    )

    def handle(self, *args, **options):
        period = first_of_month(timezone.localdate())
        for organization in Organization.objects.filter(is_active=True):
            created, _ = generate_rent_invoices(organization, period)
            fees = apply_late_fees(organization)
            if created or fees:
                self.stdout.write(f"{organization.name}: {created} invoices, {fees} late fees")
        self.stdout.write(self.style.SUCCESS(f"Billing run for {period:%B %Y} complete."))
