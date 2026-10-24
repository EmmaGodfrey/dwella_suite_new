
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.common.permissions import IsPlatformAdmin, IsPlatformSuperuser

pytestmark = pytest.mark.django_db

@pytest.mark.parametrize(
    "staff,superuser,allowed_admin,allowed_superuser",
    [
        (False, False, False, False),
        (True, False, True, False),
        (False, True, True, True),
        (True, True, True, True),
    ],
)
def test_platform_permission_roles(staff, superuser, allowed_admin, allowed_superuser):
    request = APIRequestFactory().get("/")
    request.user = get_user_model().objects.create_user(
        username="platform-permission", is_staff=staff, is_superuser=superuser
    )
    assert IsPlatformAdmin().has_permission(request, None) is allowed_admin
    assert IsPlatformSuperuser().has_permission(request, None) is allowed_superuser
