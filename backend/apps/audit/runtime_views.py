import ipaddress
import socket
import ssl
from http.client import HTTPSConnection
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

from django.db import transaction
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.common.permissions import IsPlatformSuperuser

from .models import PlatformSettings
from .runtime_serializers import RuntimeSettingsSerializer, readiness
from .runtime_settings import public_settings, runtime_settings, safe_assistant_url
from .services import record_event


class ConfigurationWriteThrottle(UserRateThrottle):
    scope = "configuration_write"
    rate = "30/hour"


class ConnectionCheckThrottle(UserRateThrottle):
    scope = "configuration_check"
    rate = "6/hour"


def payload(instance):
    return {"values": RuntimeSettingsSerializer(instance).data, "readiness": readiness(instance)}


class RuntimeSettingsView(APIView):
    permission_classes = [IsPlatformSuperuser]

    def get_throttles(self):
        return [ConfigurationWriteThrottle()] if self.request.method == "PATCH" else []

    def get(self, request):
        instance = PlatformSettings.objects.filter(pk=1).first() or PlatformSettings(pk=1)
        return Response(payload(instance), headers={"Cache-Control": "private, no-store"})

    @transaction.atomic
    def patch(self, request):
        PlatformSettings.objects.get_or_create(pk=1)
        instance = PlatformSettings.objects.select_for_update().get(pk=1)
        serializer = RuntimeSettingsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_event(
            request,
            "platform.runtime_settings_updated",
            instance,
            fields=sorted(serializer.validated_data),
        )
        return Response(payload(instance), headers={"Cache-Control": "private, no-store"})


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PinnedHTTPSConnection(HTTPSConnection):
    """Connect to the checked public IP while verifying TLS against the approved host."""

    def __init__(self, host, *, pinned_ip, context=None, **kwargs):
        self.pinned_ip = pinned_ip
        self.verified_context = context or ssl.create_default_context()
        super().__init__(host, context=self.verified_context, **kwargs)

    def connect(self):
        raw = socket.create_connection(
            (self.pinned_ip, self.port), self.timeout, self.source_address
        )
        try:
            self.sock = self.verified_context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


class PinnedHTTPSHandler(HTTPSHandler):
    def __init__(self, address):
        super().__init__(context=ssl.create_default_context())
        self.address = address

    def https_open(self, req):
        def connection(host, **kwargs):
            return PinnedHTTPSConnection(host, pinned_ip=self.address, **kwargs)

        return self.do_open(connection, req, context=self._context)


def verify_assistant_connection(url):
    if not safe_assistant_url(url):
        raise serializers.ValidationError({"assistant_url": "Use an approved HTTPS address."})
    host = urlsplit(url).hostname
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise ValueError("Non-public address")
        opener = build_opener(
            ProxyHandler({}), NoRedirect(), PinnedHTTPSHandler(addresses[0][4][0])
        )
        with opener.open(Request(url, headers={"Accept": "application/json"}), timeout=5) as reply:
            if reply.status != 200:
                raise ValueError("Unavailable")
    except HTTPError as error:
        # Authentication is expected; the HTTPS handshake still proves the host.
        if error.code not in (401, 403):
            raise serializers.ValidationError(
                {"assistant_url": "The approved endpoint did not answer successfully."}
            ) from None
    except (URLError, OSError, ValueError):
        raise serializers.ValidationError(
            {"assistant_url": "HTTPS verification failed. Check the certificate and endpoint."}
        ) from None


class AssistantConnectionCheckView(APIView):
    permission_classes = [IsPlatformSuperuser]
    throttle_classes = [ConnectionCheckThrottle]

    def post(self, request):
        if request.data:
            raise serializers.ValidationError(
                "This checks the saved address; no payload is needed."
            )
        instance = PlatformSettings.objects.filter(pk=1).first() or PlatformSettings(pk=1)
        url = runtime_settings(instance=instance)["assistant_url"]
        # TLS/DNS happens outside the transaction, without an identity token.
        verify_assistant_connection(url)
        with transaction.atomic():
            PlatformSettings.objects.get_or_create(pk=1)
            instance = PlatformSettings.objects.select_for_update().get(pk=1)
            if runtime_settings(instance=instance)["assistant_url"] != url:
                raise serializers.ValidationError(
                    "The address changed. Check the saved address again."
                )
            instance.runtime_config = {**instance.runtime_config, "assistant_verified_url": url}
            instance.save(update_fields=["runtime_config"])
            record_event(request, "platform.assistant_connection_verified", instance)
        return Response(payload(instance), headers={"Cache-Control": "private, no-store"})


class PublicConfigurationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    class PublicConfigurationThrottle(AnonRateThrottle):
        scope = "public_configuration"
        rate = "120/hour"

    throttle_classes = [PublicConfigurationThrottle]

    def get(self, request):
        return Response(public_settings(), headers={"Cache-Control": "no-store"})
