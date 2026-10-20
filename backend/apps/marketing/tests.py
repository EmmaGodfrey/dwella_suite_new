import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from .models import BetaApplication

URL = "/api/v1/marketing/beta-applications/"
ADMIN_URL = "/api/v1/marketing/admin/beta-applications/"
User = get_user_model()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.mark.django_db
def test_beta_application_is_stored_and_enveloped():
    response = APIClient().post(
        URL,
        {
            "name": "Bwalya Mulenga",
            "phone": "097 123 4567",
            "email": "bwalya@example.com",
            "role": "Landlord",
            "units": "6-20",
            "town": "Lusaka",
        },
        format="json",
    )

    assert response.status_code == 201
    assert BetaApplication.objects.filter(email="bwalya@example.com").exists()
    payload = response.json()
    assert payload["success"] is True
    assert payload["response_code"] == 201
    assert payload["response_data"]["application_id"]


@pytest.mark.django_db
def test_beta_application_rejects_invalid_input():
    response = APIClient().post(
        URL,
        {"name": "B", "phone": "123", "role": "Other", "units": "1-5"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert BetaApplication.objects.count() == 0


@pytest.mark.django_db
def test_beta_application_is_rate_limited():
    client = APIClient()
    data = {
        "name": "Bwalya Mulenga",
        "phone": "097 123 4567",
        "role": "Landlord",
        "units": "1-5",
    }

    for _ in range(5):
        assert client.post(URL, data, format="json").status_code == 201
    assert client.post(URL, data, format="json").status_code == 429


@pytest.mark.django_db
def test_only_platform_admins_can_list_beta_applications():
    BetaApplication.objects.create(
        name="Bwalya Mulenga",
        phone="097 123 4567",
        role="Landlord",
        units="1-5",
    )
    client = APIClient()
    assert client.get(ADMIN_URL).status_code == 403

    user = User.objects.create_user(username="landlord", password="StrongerPass123")
    client.force_authenticate(user)
    assert client.get(ADMIN_URL).status_code == 403

    user.is_staff = True
    user.save(update_fields=["is_staff"])
    response = client.get(ADMIN_URL)
    assert response.status_code == 200
    assert response.json()["response_data"][0]["name"] == "Bwalya Mulenga"


@pytest.mark.django_db
def test_platform_admin_can_update_signup_follow_up():
    application = BetaApplication.objects.create(
        name="Bwalya Mulenga",
        phone="097 123 4567",
        role="Landlord",
        units="1-5",
    )
    admin = User.objects.create_superuser(
        username="admin@example.com",
        email="admin@example.com",
        password="StrongerPass123",
    )
    client = APIClient()
    client.force_authenticate(admin)

    response = client.patch(
        f"{ADMIN_URL}{application.pk}/",
        {"status": "contacted", "internal_notes": "Requested a product demo."},
        format="json",
    )

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.status == BetaApplication.Status.CONTACTED
    assert application.internal_notes == "Requested a product demo."


@pytest.mark.django_db
def test_rate_limit_counts_each_visitor_behind_the_proxy(settings):
    # Production sits behind one Nginx hop: visitors must not share a limit,
    # and a forged X-Forwarded-For entry must not buy a fresh one.
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}
    data = {"name": "Bwalya Mulenga", "phone": "097 123 4567", "role": "Landlord", "units": "1-5"}
    first, second = APIClient(), APIClient()

    for _ in range(5):
        response = first.post(URL, data, format="json", HTTP_X_FORWARDED_FOR="41.1.1.1")
        assert response.status_code == 201
    assert first.post(URL, data, format="json", HTTP_X_FORWARDED_FOR="41.1.1.1").status_code == 429
    spoofed = first.post(URL, data, format="json", HTTP_X_FORWARDED_FOR="9.9.9.9, 41.1.1.1")
    assert spoofed.status_code == 429
    assert second.post(URL, data, format="json", HTTP_X_FORWARDED_FOR="41.2.2.2").status_code == 201
