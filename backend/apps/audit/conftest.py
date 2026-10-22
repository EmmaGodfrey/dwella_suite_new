
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.organizations.models import Organization

pytestmark = pytest.mark.django_db

@pytest.fixture
def context():
    cache.clear()
    user = get_user_model().objects.create_user(username="support-admin", is_staff=True)
    org = Organization.objects.create(name="First support workspace")
    other = Organization.objects.create(name="Other support workspace")
    client = APIClient()
    client.force_authenticate(user)
    return client, user, org, other
