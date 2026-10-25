import importlib

from django.contrib.auth.models import AnonymousUser
from django.core.cache import CacheHandler
from django.test import override_settings
from rest_framework.test import APIRequestFactory
from rest_framework.throttling import AnonRateThrottle


def test_configured_redis_is_the_shared_throttle_backend(monkeypatch):
    monkeypatch.setenv("APP_CACHE_URL", "redis://redis:6379/1")
    # Load a separate settings module without changing the running test settings.
    spec = importlib.util.find_spec("config.settings")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with override_settings(CACHES=module.CACHES):
        backend = CacheHandler()["default"]
        assert backend.__class__.__name__ == "RedisCache"
        assert backend._servers == ["redis://redis:6379/1"]


def test_separate_throttle_instances_share_the_same_limit():
    request = APIRequestFactory().get("/", REMOTE_ADDR="192.0.2.71")
    request.user = AnonymousUser()

    class OneRequestThrottle(AnonRateThrottle):
        rate = "1/minute"
        scope = "shared_backend_regression"

    first, second = OneRequestThrottle(), OneRequestThrottle()
    key = first.get_cache_key(request, None)
    first.cache.delete(key)
    try:
        assert first.allow_request(request, None)
        assert not second.allow_request(request, None)
    finally:
        first.cache.delete(key)
