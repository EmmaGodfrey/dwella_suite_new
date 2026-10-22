from uuid import uuid4

from django.db import transaction

from .models import Organization, OrganizationMembership


@transaction.atomic
def create_workspace(owner, *, display_name, **profile):
    organization = Organization.objects.create(
        name=f"workspace-{uuid4().hex}", display_name=display_name, **profile,
    )
    OrganizationMembership.objects.create(organization=organization, user=owner, role="owner")
    return organization
