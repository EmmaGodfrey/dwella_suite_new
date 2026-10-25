from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework.throttling import AnonRateThrottle


@pytest.mark.django_db
def test_monitoring_bypasses_exhausted_public_limits_without_resetting_auth_limits():
    cache.clear()
    client = APIClient(REMOTE_ADDR="192.0.2.93")
    try:
        with patch.object(AnonRateThrottle, "rate", "1/hour", create=True):
            assert client.post("/api/v1/accounts/login/", {}, format="json").status_code == 400
            assert client.post("/api/v1/accounts/login/", {}, format="json").status_code == 429
            for _ in range(120):
                response = client.get("/api/health/")
                assert response.status_code == 200
                assert response.json()["response_data"]["status"] == "ok"
            assert client.post("/api/v1/accounts/login/", {}, format="json").status_code == 429
    finally:
        cache.clear()
