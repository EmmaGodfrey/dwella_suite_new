import csv
from io import StringIO

from django.db.models import Q
from django.http import HttpResponse
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from apps.common.permissions import IsPlatformAdmin
from apps.common.serializers import PublicIdModelSerializer

from .models import AuditEvent


class AuditEventSerializer(PublicIdModelSerializer):
    actor_name = serializers.SerializerMethodField()
    actor_email = serializers.EmailField(source="actor.email", default="", read_only=True)
    workspace_id = serializers.UUIDField(source="organization.public_id", allow_null=True,
                                        read_only=True)
    workspace_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = ["id", "actor_id", "actor_name", "actor_email", "workspace_id", "workspace_name",
                  "action", "resource_type", "resource_id", "request_id", "metadata", "created_at"]
        read_only_fields = fields

    def get_actor_name(self, obj):
        return (obj.actor.get_full_name() or obj.actor.email or obj.actor.username
                if obj.actor else "Deleted user / system")

    def get_workspace_name(self, obj):
        return str(obj.organization) if obj.organization_id else ""


class EventFilters(serializers.Serializer):
    actor = serializers.IntegerField(min_value=1, required=False)
    user = serializers.IntegerField(min_value=1, required=False)
    workspace = serializers.UUIDField(required=False)
    support_session = serializers.UUIDField(required=False)
    action = serializers.CharField(max_length=120, required=False)
    resource_type = serializers.CharField(max_length=120, required=False)
    resource_id = serializers.CharField(max_length=120, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, data):
        if data.get("date_from") and data.get("date_to") and data["date_from"] > data["date_to"]:
            raise ValidationError("Start date must not be after end date.")
        return data


def csv_cell(value):
    text = str(value or "")
    unsafe = text.startswith(("\t", "\r", "\n")) or text.lstrip().startswith(("=", "+", "-", "@"))
    return "'" + text if unsafe else text


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = AuditEventSerializer
    lookup_field = "public_id"
    search_fields = ["action", "actor__email", "organization__display_name", "request_id"]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        data = EventFilters(data=dict(self.request.query_params.items()))
        data.is_valid(raise_exception=True)
        query = AuditEvent.objects.select_related("actor", "organization").order_by(
            "-created_at", "-pk",
        )
        mapping = {"actor": "actor_id", "workspace": "organization__public_id",
                   "support_session": "metadata__support_session", "action": "action",
                   "resource_type": "resource_type", "resource_id": "resource_id",
                   "date_from": "created_at__date__gte", "date_to": "created_at__date__lte"}
        for key, field in mapping.items():
            if key in data.validated_data:
                value = data.validated_data[key]
                query = query.filter(**{field: str(value) if key == "support_session" else value})
        if user := data.validated_data.get("user"):
            query = query.filter(
                Q(actor_id=user) | Q(resource_type="auth.user", resource_id=str(user))
                | Q(metadata__user_id=user),
            )
        return query

    @action(detail=False, methods=["get"])
    def export(self, request):
        query = self.filter_queryset(self.get_queryset())
        if query.count() > 10000:
            raise ValidationError("Narrow the filters to export at most 10,000 audit events.")
        stream = StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["Time", "Actor", "Workspace", "Action", "Resource", "Resource ID",
                         "Support session", "Reason", "Request ID"])
        for event in query.iterator(chunk_size=500):
            writer.writerow([csv_cell(value) for value in [event.created_at.isoformat(),
                event.actor.email if event.actor else "", str(event.organization or ""),
                event.action,
                event.resource_type, event.resource_id, event.metadata.get("support_session", ""),
                event.metadata.get("reason", ""), event.request_id]])
        response = HttpResponse(
            "\ufeff" + stream.getvalue(), content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="dwella-audit-log.csv"'
        response["Cache-Control"] = "private, no-store"
        return response
