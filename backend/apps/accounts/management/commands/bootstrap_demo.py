from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.organizations.models import Organization, OrganizationMembership
from apps.properties.models import Property, PropertyOwner, Unit


class Command(BaseCommand):
    help = "Creates a demo Dwella organization with sample properties and units."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@dwella.local")
        parser.add_argument("--password", default="admin12345")
        parser.add_argument("--organization", default="Dwella Demo")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"].lower()
        password = options["password"]
        organization_name = options["organization"]

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "first_name": "Dwella",
                "last_name": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])

        organization, _ = Organization.objects.get_or_create(
            name=organization_name,
            defaults={
                "display_name": organization_name,
                "email": email,
                "phone_number": "+260 970 000 000",
                "town": "Lusaka",
            },
        )

        OrganizationMembership.objects.get_or_create(
            organization=organization,
            user=user,
            defaults={"role": OrganizationMembership.Role.OWNER},
        )

        owner, _ = PropertyOwner.objects.get_or_create(
            organization=organization,
            full_name="Mulenga Holdings",
            defaults={
                "email": "owner@dwella.local",
                "phone_number": "+260 971 111 111",
                "address": "Great East Road, Lusaka",
            },
        )

        property_one, _ = Property.objects.get_or_create(
            organization=organization,
            name="Kabulonga Heights",
            defaults={
                "owner": owner,
                "property_type": Property.PropertyType.APARTMENT,
                "address": "Kabulonga Road",
                "town": "Lusaka",
                "province": "Lusaka",
                "description": "A managed residential apartment block.",
            },
        )

        property_two, _ = Property.objects.get_or_create(
            organization=organization,
            name="Makeni Retail Park",
            defaults={
                "owner": owner,
                "property_type": Property.PropertyType.COMMERCIAL,
                "address": "Makeni",
                "town": "Lusaka",
                "province": "Lusaka",
                "description": "Commercial units for retail tenants.",
            },
        )

        units = [
            (property_one, "A1", Decimal("6500.00"), Unit.OccupancyStatus.OCCUPIED),
            (property_one, "A2", Decimal("6500.00"), Unit.OccupancyStatus.VACANT),
            (property_two, "Shop 01", Decimal("12000.00"), Unit.OccupancyStatus.OCCUPIED),
        ]

        for property_obj, name, rent_amount, status in units:
            Unit.objects.get_or_create(
                organization=organization,
                property=property_obj,
                name=name,
                defaults={
                    "bedrooms": 2 if property_obj == property_one else 0,
                    "bathrooms": Decimal("1.0"),
                    "rent_amount": rent_amount,
                    "occupancy_status": status,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo ready: {email} / {password} in organization '{organization}'."
            )
        )
