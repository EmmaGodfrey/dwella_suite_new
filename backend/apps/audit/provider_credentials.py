"""Replace-only credentials. No API ever returns a saved value."""

import hmac
import json
import time

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from rest_framework import serializers
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import TwoFactorDevice
from apps.accounts.security import _hotp
from apps.common.permissions import IsPlatformSuperuser

from .models import ProviderCredential, ProviderCredentialProof
from .services import record_event

# The key names double as environment defaults; requests cannot choose arbitrary settings.
FIELDS = {
    "AFRICASTALKING_API_KEY": ("sms", "API key", 16, 512),
    "AFRICASTALKING_CALLBACK_TOKEN": ("sms", "Callback token", 32, 512),
    "RESEND_API_KEY": ("email", "API key", 16, 512),
    "WHATSAPP_ACCESS_TOKEN": ("whatsapp", "Access token", 20, 8192),
    "WHATSAPP_APP_SECRET": ("whatsapp", "App secret", 32, 512),
    "WHATSAPP_VERIFY_TOKEN": ("whatsapp", "Verification token", 32, 512),
}
UNAVAILABLE = "Provider credential storage is unavailable. Contact the server administrator."


class CredentialStoreUnavailable(APIException):
    status_code = 503
    default_detail = UNAVAILABLE


def cipher():
    keys = [
        settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY,
        *settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY_FALLBACKS,
    ]
    try:
        if not keys[0]:
            raise ValueError
        return MultiFernet([Fernet(key) for key in keys])
    except (ValueError, TypeError):
        raise CredentialStoreUnavailable() from None


@sensitive_variables("values", "rows", "value", "document")
def provider_credentials(*names, alias="default"):
    if any(name not in FIELDS for name in names):
        raise ValueError("Unknown provider credential")
    values = {name: getattr(settings, name, "") for name in names}
    if not settings.PROVIDER_CREDENTIALS_ENABLED:
        return values
    crypto = cipher()  # Never silently fall back when an enabled store is unreadable.
    rows = ProviderCredential.objects.using(alias).filter(name__in=names)
    for row in rows:
        try:
            document = json.loads(crypto.decrypt(bytes(row.encrypted_value)))
            if document["name"] != row.name or not isinstance(document["value"], str):
                raise ValueError
            values[row.name] = document["value"]
        except (InvalidToken, ValueError, KeyError, TypeError):
            raise CredentialStoreUnavailable() from None
    return values


def credential(name, *, alias="default"):
    return provider_credentials(name, alias=alias)[name]


def metadata():
    rows = {row.name: row for row in ProviderCredential.objects.all().only("name", "updated_at")}
    return {
        "replacement_available": bool(
            settings.PROVIDER_CREDENTIALS_ENABLED and settings.PROVIDER_CREDENTIAL_ENCRYPTION_KEY
        ),
        "credentials": [
            {
                "name": name,
                "provider": spec[0],
                "label": spec[1],
                "min_length": spec[2],
                "max_length": spec[3],
                "configured": name in rows or bool(getattr(settings, name, "")),
                "source": "saved"
                if name in rows
                else "environment"
                if getattr(settings, name, "")
                else "missing",
                "updated_at": rows[name].updated_at if name in rows else None,
            }
            for name, spec in FIELDS.items()
        ],
    }


class ReplacementSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)
    code = serializers.RegexField(r"^[0-9]{6}$", write_only=True)
    values = serializers.DictField(
        child=serializers.CharField(max_length=8192, trim_whitespace=False, write_only=True),
        write_only=True,
    )

    def validate(self, attrs):
        if set(self.initial_data) != {"password", "code", "values"}:
            raise serializers.ValidationError(
                "Supply only the new credentials, password and authenticator code."
            )
        values = attrs["values"]
        if not values or set(values) - FIELDS.keys():
            raise serializers.ValidationError({"values": "Choose supported provider credentials."})
        for name, value in values.items():
            _, _, minimum, maximum = FIELDS[name]
            if not minimum <= len(value) <= maximum or any(
                ord(c) < 33 or ord(c) > 126 for c in value
            ):
                raise serializers.ValidationError(
                    {"values": "Use complete credentials without spaces or control characters."}
                )
        return attrs


@sensitive_variables("password", "code", "values", "user", "device", "document")
@transaction.atomic
def replace_credentials(request, *, password, code, values):
    if not settings.PROVIDER_CREDENTIALS_ENABLED:
        raise serializers.ValidationError(UNAVAILABLE)
    crypto = cipher()
    # Lock the actor first: serializes concurrent proofs and rechecks revoked privileges.
    user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
    device = (
        TwoFactorDevice.objects.select_for_update().filter(user=user, is_confirmed=True).first()
    )
    if (
        not user.is_active
        or not user.is_superuser
        or not user.check_password(password)
        or not device
    ):
        raise PermissionDenied("Confirm your current password and a configured authenticator.")
    counter = int(time.time() // 30)
    matches = [
        tick
        for tick in range(counter - 1, counter + 2)
        if hmac.compare_digest(_hotp(device.secret, tick), code)
    ]
    proof, _ = ProviderCredentialProof.objects.get_or_create(user=user)
    if not matches or max(matches) <= proof.last_counter:
        raise PermissionDenied("Use a fresh authenticator code and try again.")
    proof.last_counter = max(matches)
    proof.save(update_fields=["last_counter"])
    for name in sorted(values):
        document = json.dumps({"name": name, "value": values[name]}).encode()
        ProviderCredential.objects.update_or_create(
            name=name, defaults={"encrypted_value": crypto.encrypt(document), "updated_by": user}
        )
    record_event(request, "platform.provider_credentials_replaced", fields=sorted(values))


class CredentialWriteThrottle(UserRateThrottle):
    scope = "provider_credential_write"
    rate = "6/hour"


@method_decorator(sensitive_post_parameters("password", "code", "values"), name="dispatch")
class ProviderCredentialsView(APIView):
    permission_classes = [IsPlatformSuperuser]

    def get_throttles(self):
        return (
            [CredentialWriteThrottle()]
            if self.request.method == "POST"
            else super().get_throttles()
        )

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response

    def get(self, request):
        return Response(metadata())

    @sensitive_variables()
    def post(self, request):
        serializer = ReplacementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        replace_credentials(request, **serializer.validated_data)
        return Response(metadata())
