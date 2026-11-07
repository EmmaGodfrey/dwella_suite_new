import pytest
from django.db import transaction

from apps.maintenance.models import MaintenanceRequest
from apps.organizations.models import Organization
from apps.properties.models import Property

from .references import next_reference

pytestmark = pytest.mark.django_db


def allocate(org):
    with transaction.atomic():
        return next_reference(org, MaintenanceRequest, "MR")


def make(org, home, reference):
    MaintenanceRequest.objects.create(
        organization=org, property=home, reference=reference, title="Leak"
    )


def test_numbers_continue_past_four_digits_and_ignore_other_shapes():
    org = Organization.objects.create(name="References")
    other = Organization.objects.create(name="Elsewhere")
    home = Property.objects.create(organization=org, name="Home", address="Plot 1")
    away = Property.objects.create(organization=other, name="Away", address="Plot 2")
    assert allocate(org) == "MR-0001"
    for reference in ["MR-0009", "MR-9999", "MR-10000", "MR-legacy", "XX-99999"]:
        make(org, home, reference)
    make(other, away, "MR-50000")
    assert allocate(org) == "MR-10001"

