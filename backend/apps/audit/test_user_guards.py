from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.organizations.models import OrganizationMembership

from .user_services import change_membership, protect_account, require_superuser

pytestmark = pytest.mark.django_db


def test_staff_cannot_grant_superuser_actions_and_self_is_protected(context):
    _, actor, _, _ = context
    request = SimpleNamespace(user=actor)
    with pytest.raises(PermissionDenied):
        require_superuser(request)
    with pytest.raises(ValidationError):
        protect_account(request, actor)


def test_last_superuser_protected_even_from_staff(context):
    _, actor, _, _ = context
    target = get_user_model().objects.create_user(username="root", is_superuser=True)
    with pytest.raises(ValidationError):
        protect_account(SimpleNamespace(user=actor), target)


@pytest.mark.parametrize("role,remove", [("tenant", False), ("landlord", True)])
def test_last_landlord_cannot_be_removed_or_demoted(context, role, remove):
    _, actor, org, _ = context
    owner = get_user_model().objects.create_user(username="owner")
    OrganizationMembership.objects.create(user=owner, organization=org, role="landlord")
    with pytest.raises(ValidationError):
        change_membership(SimpleNamespace(user=actor), owner, org, role, remove)


def test_membership_changes_keep_an_active_landlord(context):
    _, actor, org, _ = context
    owner = get_user_model().objects.create_user(username="owner")
    another = get_user_model().objects.create_user(username="another")
    OrganizationMembership.objects.create(user=owner, organization=org, role="landlord")
    request = SimpleNamespace(user=actor)
    change_membership(request, another, org, "landlord")
    changed = change_membership(request, owner, org, "tenant")
    assert changed.role == "tenant"
    changed = change_membership(request, owner, org, "tenant", remove=True)
    assert changed.is_active is False
    org.is_active = False
    org.save()
    with pytest.raises(ValidationError):
        change_membership(request, another, org, "tenant")
