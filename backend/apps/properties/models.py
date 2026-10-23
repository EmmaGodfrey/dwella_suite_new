from uuid import uuid4

from django.db import models

from apps.common.models import OrganizationScopedModel

from .managers import PropertyManager


def property_cover_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"properties/covers/{uuid4().hex}.{extension}"


class Property(OrganizationScopedModel):
    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        HOUSE = "house", "House"
        COMMERCIAL = "commercial", "Commercial"
        MIXED_USE = "mixed_use", "Mixed Use"
        LAND = "land", "Land"

    class ManagementStatus(models.TextChoices):
        MANAGED = "managed", "Managed"
        PROSPECT = "prospect", "Prospect"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=180)
    property_type = models.CharField(max_length=30, choices=PropertyType.choices)
    management_status = models.CharField(
        max_length=30,
        choices=ManagementStatus.choices,
        default=ManagementStatus.MANAGED,
        db_index=True,
    )
    address = models.TextField()
    town = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to=property_cover_path, blank=True, null=True)

    objects = PropertyManager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "properties"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_property_name_per_organization",
            )
        ]

    def __str__(self):
        return self.name


class Unit(OrganizationScopedModel):
    class OccupancyStatus(models.TextChoices):
        VACANT = "vacant", "Vacant"
        OCCUPIED = "occupied", "Occupied"
        MAINTENANCE = "maintenance", "Maintenance"
        RESERVED = "reserved", "Reserved"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="units")
    name = models.CharField(max_length=80)
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    floor_area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2)
    occupancy_status = models.CharField(
        max_length=30,
        choices=OccupancyStatus.choices,
        default=OccupancyStatus.VACANT,
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["property__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "name"],
                name="unique_unit_name_per_property",
            )
        ]

    def __str__(self):
        return f"{self.property} - {self.name}"
