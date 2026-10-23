import secrets
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.leases.models import Lease
from apps.leases.services import create_lease
from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, Unit
from apps.tenants.models import Tenant

PROPERTIES = [
    (
        "Mutendere Court",
        "apartment",
        "Plot 4471, Mutendere East",
        [("1A", 3900), ("1B", 3900), ("2A", 3900), ("2B", 3900), ("3A", 5400), ("3B", 5400)],
    ),
    ("Riverside Flats", "apartment", "Kafue Road", [("A1", 7200), ("A2", 5400), ("B1", 5400)]),
]

# name, phone, unit, months already into a 12-month lease (None = no lease), active?
TENANTS = [
    ("Natasha Banda", "+260972231180", "1A", 3, True),
    ("Mutale Phiri", "+260957810092", "1B", 7, True),
    ("Chanda Mwila", "+260974123381", "2A", 6, True),
    ("Lubasi Nyirenda", "+260976634410", "2B", 10, True),
    ("Joseph Tembo", "+260962201045", "A1", 11, True),
    ("Bwalya Kasonde", "+260975512208", "A2", -1, False),
    ("Grace Mulenga", "+260967778899", None, None, False),
]


def add_months(day, months):
    month = day.month - 1 + months
    return date(day.year + month // 12, month % 12 + 1, 1)


class Command(BaseCommand):
    help = (
        "Creates a demo landlord login that owns the demo workspace, with sample "
        "properties, tenants and leases. Safe to re-run. The generated password is "
        "written to .env.demo (gitignored) at the repo root, never printed."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", default="landlord@dwella.local")
        parser.add_argument("--organization", default="Dwella Demo")
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Issue a new password even if the user exists.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        email = options["email"].lower()
        user, created = get_user_model().objects.get_or_create(
            username=email,
            defaults={"email": email, "first_name": "Emmanuel", "last_name": "Godfrey"},
        )
        if user.is_staff or user.is_superuser:
            self.stderr.write(
                f"{email} is a platform admin; choose another --email for the landlord."
            )
            return

        credentials_file = Path(settings.BASE_DIR).parent / ".env.demo"
        if created or options["reset_password"]:
            password = secrets.token_urlsafe(12)
            user.set_password(password)
            user.save(update_fields=["password"])
            credentials_file.write_text(
                f"DEMO_LANDLORD_EMAIL={email}\nDEMO_LANDLORD_PASSWORD={password}\n",
                encoding="utf-8",
            )

        organization, _ = Organization.objects.get_or_create(
            name=options["organization"], defaults={"display_name": options["organization"]}
        )
        OrganizationMembership.objects.update_or_create(
            organization=organization,
            user=user,
            defaults={"role": OrganizationMembership.Role.LANDLORD, "is_active": True},
        )

        units = {}
        for name, kind, address, unit_specs in PROPERTIES:
            property_obj, _ = Property.objects.get_or_create(
                organization=organization,
                name=name,
                defaults={
                    "property_type": kind,
                    "address": address,
                    "town": "Lusaka",
                    "province": "Lusaka",
                },
            )
            for unit_name, rent in unit_specs:
                units[unit_name], _ = Unit.objects.get_or_create(
                    organization=organization,
                    property=property_obj,
                    name=unit_name,
                    defaults={"rent_amount": Decimal(rent)},
                )

        this_month = date.today().replace(day=1)
        for full_name, phone, unit_name, months_in, active in TENANTS:
            tenant, _ = Tenant.objects.get_or_create(
                organization=organization,
                phone_number=phone,
                defaults={
                    "full_name": full_name,
                    "email": f"{full_name.split()[0].lower()}@example.com",
                },
            )
            if unit_name is None or tenant.leases.exists():
                continue
            unit = units[unit_name]
            if Lease.objects.filter(unit=unit, status__in=Lease.OPEN_STATUSES).exists():
                continue
            start = add_months(this_month, -months_in)
            create_lease(
                organization=organization,
                tenant=tenant,
                unit=unit,
                start_date=start,
                end_date=add_months(start, 12) - timedelta(days=1),
                monthly_rent=unit.rent_amount,
                deposit_amount=unit.rent_amount * 2,
                late_fee_percent=Decimal("5"),
                activate=active,
            )

        where = (
            credentials_file
            if (created or options["reset_password"])
            else "unchanged (use --reset-password)"
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo landlord {email} owns '{organization.name}'. Login details: {where}"
            )
        )
