from rest_framework import generics, serializers

from apps.common.permissions import CanViewPortfolio, IsPlatformSuperuser
from apps.common.workspaces import resolve_workspace

from .models import OperationalDelivery


class OperationalDeliverySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)
    subject = serializers.SerializerMethodField()
    workspace_name = serializers.CharField(source="organization.name", read_only=True)
    recipient_name = serializers.CharField(source="recipient", read_only=True)

    def get_subject(self, obj):
        from .operational import TITLES

        return TITLES.get(obj.event, "Dwella update")

    class Meta:
        model = OperationalDelivery
        fields = [
            "subject",
            "workspace_name",
            "recipient_name",
            "id",
            "event",
            "audience",
            "channel",
            "recipient",
            "status",
            "reason",
            "attempts",
            "created_at",
            "sent_at",
        ]
        read_only_fields = fields


class OperationalMessagesView(generics.ListAPIView):
    permission_classes = [CanViewPortfolio]
    serializer_class = OperationalDeliverySerializer
    filterset_fields = ["channel", "status", "event"]
    search_fields = ["event", "recipient"]

    def get_queryset(self):
        return (
            OperationalDelivery.objects.filter(
                organization=resolve_workspace(self.request),
            )
            .select_related("organization")
            .order_by("-created_at", "-pk")
        )

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class PlatformOperationalMessagesView(OperationalMessagesView):
    permission_classes = [IsPlatformSuperuser]

    def get_queryset(self):
        return OperationalDelivery.objects.select_related("organization").order_by(
            "-created_at", "-pk"
        )
