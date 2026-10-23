import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from rest_framework.test import APIClient

from .models import OutreachSettings


@pytest.fixture
def staff():
    cache.clear()
    user = get_user_model().objects.create_user(username="outreach-review", is_staff=True)
    client = APIClient()
    client.force_authenticate(user)
    call_command("seed_outreach_templates", verbosity=0)
    OutreachSettings.objects.filter(pk=1).update(
        sender_first_name="Test sender",
        signature="Test sender, EG Labs",
        signature_short="Test sender",
        offer="A test offer",
    )
    return client, user
