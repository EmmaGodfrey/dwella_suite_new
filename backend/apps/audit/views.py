from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.common.permissions import IsPlatformAdmin
from apps.organizations.models import Organization

from .models import SupportSession
from .serializers import SupportSessionSerializer
from .services import record_event


class SupportSessionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsPlatformAdmin]
    serializer_class = SupportSessionSerializer
    lookup_field = "public_id"
    lookup_url_kwarg = "public_id"

    def get_throttles(self):
        self.throttle_scope = "support_session" if self.action == "create" else None
        return super().get_throttles()

    def get_queryset(self):
        return SupportSession.objects.filter(admin=self.request.user).select_related("organization")

    def list(self, request):
        query = self.get_queryset()
        active = request.query_params.get("active")
        if active not in (None, "true", "false"):
            raise serializers.ValidationError({"active": "Use true or false."})
        if active == "true":
            query = query.filter(ended_at__isnull=True, expires_at__gt=timezone.now())
        elif active == "false":
            from django.db.models import Q

            query = query.filter(Q(ended_at__isnull=False) | Q(expires_at__lte=timezone.now()))
        page = self.paginate_queryset(query)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @transaction.atomic
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = Organization.objects.select_for_update().get(
            pk=serializer.validated_data["organization"].pk,
        )
        if not organization.is_active:
            raise serializers.ValidationError({"organization": "This workspace is suspended."})
        session = serializer.save(
            admin=request.user, expires_at=timezone.now() + timedelta(hours=4)
        )
        record_event(
            request,
            "support_session.started",
            session,
            organization=session.organization,
            support_session=str(session.public_id),
            reason=session.reason,
        )
        request._request.support_event_recorded = True
        return Response(self.get_serializer(session).data, status=201)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def end(self, request, public_id=None):
        session = get_object_or_404(self.get_queryset().select_for_update(), public_id=public_id)
        if session.ended_at is None:
            session.ended_at = timezone.now()
            session.save(update_fields=["ended_at", "updated_at"])
            record_event(
                request,
                "support_session.ended",
                session,
                organization=session.organization,
                support_session=str(session.public_id),
                reason=session.reason,
            )
        request._request.support_event_recorded = True
        return Response(self.get_serializer(session).data)
