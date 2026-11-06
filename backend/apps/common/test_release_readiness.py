from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from django.utils import timezone

from apps.accounts.models import TwoFactorDevice
from apps.scheduler.models import JobRun

from .release_readiness import snapshot

pytestmark = pytest.mark.django_db


def good(settings):
    settings.DEBUG = False
    settings.NATIVE_ADMIN_ENABLED = False
    settings.REQUIRE_ADMIN_MFA = True
    user = get_user_model().objects.create_user(username="ready-admin", is_staff=True)
    TwoFactorDevice.objects.create(user=user, secret="synthetic", is_confirmed=True)
    JobRun.objects.create(
        job="offsite_backups",
        status="succeeded",
        started_at=timezone.now() - timedelta(minutes=5),
        finished_at=timezone.now() - timedelta(minutes=4),
    )


def test_all_readiness_facts_are_required_and_no_account_details_leak(settings):
    good(settings)
    with patch("apps.common.release_readiness.call_command"):
        result = snapshot()
    assert result["ready"] and all(result["checks"].values())
    assert "ready-admin" not in str(result)


@pytest.mark.parametrize("change", ["mfa", "backup", "database", "debug", "admin"])
def test_readiness_fails_closed_on_each_critical_dependency(settings, change):
    good(settings)
    if change == "mfa":
        TwoFactorDevice.objects.update(is_confirmed=False)
    elif change == "backup":
        JobRun.objects.update(finished_at=timezone.now() - timedelta(hours=3))
    elif change == "debug":
        settings.DEBUG = True
    elif change == "admin":
        settings.NATIVE_ADMIN_ENABLED = True
    with patch(
        "apps.common.release_readiness.call_command",
        side_effect=CommandError("unsafe") if change == "database" else None,
    ):
        assert not snapshot()["ready"]


def test_stale_whatsapp_worker_or_unapproved_code_template_blocks_whatsapp_release(settings):
    good(settings)
    with (
        patch("apps.common.release_readiness.call_command"),
        patch(
            "apps.notifications.phone_codes.ready",
            return_value=False,
        ),
        patch(
            "apps.notifications.whatsapp.wakeup.heartbeats",
            return_value={"fast": None, "files": None, "notices": None},
        ),
    ):
        result = snapshot(require_whatsapp=True)
    assert not result["ready"] and not result["checks"]["whatsapp_verification_ready"]
    assert not result["checks"]["whatsapp_files_worker_fresh"]
