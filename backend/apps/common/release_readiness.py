"""Bounded read-only readiness facts. Never include contacts, message bodies or keys."""

from datetime import timedelta
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.accounts.models import TwoFactorDevice
from apps.scheduler.models import JobRun


def snapshot(*, require_whatsapp=False):
    now = timezone.now()
    confirmed = TwoFactorDevice.objects.filter(user_id=OuterRef("pk"), is_confirmed=True)
    privileged = (
        get_user_model()
        .objects.filter(is_active=True)
        .filter(
            Q(is_staff=True) | Q(is_superuser=True),
        )
    )
    missing = privileged.alias(confirmed=Exists(confirmed)).filter(confirmed=False).count()
    try:
        call_command("check_runtime_database", stdout=StringIO())
    except CommandError:
        restricted = False
    else:
        restricted = True
    backup = JobRun.objects.filter(job="offsite_backups").order_by("-started_at").first()
    checks = {
        "debug_disabled": not settings.DEBUG,
        "native_admin_disabled": not settings.NATIVE_ADMIN_ENABLED,
        "administrator_mfa_required": settings.REQUIRE_ADMIN_MFA,
        "administrator_mfa_enrolled": missing == 0,
        "restricted_runtime_database": restricted,
        "recent_successful_offsite_backup": bool(
            backup
            and backup.status == "succeeded"
            and backup.finished_at
            and now - timedelta(hours=2) <= backup.finished_at <= now
        ),
    }
    if require_whatsapp:
        from apps.notifications.phone_codes import ready
        from apps.notifications.whatsapp.wakeup import heartbeats

        checks["whatsapp_verification_ready"] = ready()
        for lane, stamp in heartbeats().items():
            try:
                value = timezone.datetime.fromisoformat(stamp)
                fresh = timezone.is_aware(value) and now - timedelta(
                    seconds=60
                ) <= value <= now + timedelta(seconds=5)
            except (TypeError, ValueError):
                fresh = False
            checks[f"whatsapp_{lane}_worker_fresh"] = fresh
    return {"ready": all(checks.values()), "checks": checks, "administrators_missing_mfa": missing}
