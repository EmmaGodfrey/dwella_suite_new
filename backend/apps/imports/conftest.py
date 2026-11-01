import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def isolated_import_previews_and_throttles():
    # Tests reuse user/workspace IDs after rollback; their rate counters and
    # preview keys must not carry over to a different synthetic account.
    cache.clear()
    yield
    cache.clear()
