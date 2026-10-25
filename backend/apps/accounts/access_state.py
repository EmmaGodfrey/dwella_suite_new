from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from .models import AccountAccessState
from .security import normalize_email


def email_status(user, request=None):
    if not user or not user.is_authenticated:
        return {"verified": False, "required": False, "verified_at": None}
    # Permission checks ask several times per request; read the state once.
    cached = getattr(request, "_email_status", None) if request is not None else None
    if cached and cached[0] == user.pk:
        return cached[1]
    status = _email_status(user)
    if request is not None:
        request._email_status = (user.pk, status)
    return status


def _email_status(user):
    state = AccountAccessState.objects.filter(user=user).first()
    verified = bool(
        state
        and state.verified_at
        and normalize_email(user.email)
        and state.verified_email == normalize_email(user.email)
    )
    required = bool(state and state.requires_verification and not verified)
    return {
        "verified": verified,
        "required": required,
        "verified_at": state.verified_at if verified else None,
    }


def require_verified_access(user, request=None):
    if email_status(user, request)["required"]:
        raise PermissionDenied(
            {
                "message": "Verify your email address to continue.",
                "code": "email_verification_required",
            }
        )


def require_new_account_verification(user):
    AccountAccessState.objects.update_or_create(
        user=user,
        defaults={"requires_verification": True, "verified_email": "", "verified_at": None},
    )


@transaction.atomic
def mark_email_verified(user):
    state, _ = AccountAccessState.objects.select_for_update().get_or_create(user=user)
    state.requires_verification = True
    state.verified_email = normalize_email(user.email)
    state.verified_at = timezone.now()
    state.save()
    return state
