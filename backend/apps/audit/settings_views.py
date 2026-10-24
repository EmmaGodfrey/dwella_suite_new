from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsPlatformSuperuser

from .models import PlatformSettings
from .services import record_event


class PlatformSettingsSerializer(serializers.ModelSerializer):
    handy_agent_configured = serializers.SerializerMethodField()

    def get_handy_agent_configured(self, obj):
        return bool(settings.HANDY_AGENT_URL and len(settings.HANDY_AGENT_SIGNING_SECRET) >= 32)

    def validate_handy_agent_enabled(self, value):
        if value and not self.get_handy_agent_configured(self.instance):
            raise serializers.ValidationError(
                "Configure the assistant connection for this environment before enabling it."
            )
        return value

    class Meta:
        model = PlatformSettings
        fields = ["handy_agent_enabled", "handy_agent_configured"]


class PlatformSettingsView(APIView):
    permission_classes = [IsPlatformSuperuser]

    def get(self, request):
        value, _ = PlatformSettings.objects.get_or_create(pk=1)
        return Response(PlatformSettingsSerializer(value).data)

    @transaction.atomic
    def patch(self, request):
        PlatformSettings.objects.get_or_create(pk=1)
        value = PlatformSettings.objects.select_for_update().get(pk=1)
        serializer = PlatformSettingsSerializer(value, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_event(request, "platform.settings_updated", value, **serializer.validated_data)
        return Response(serializer.data)
