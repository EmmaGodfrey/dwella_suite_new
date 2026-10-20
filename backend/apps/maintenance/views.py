from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.common.viewsets import OrganizationScopedModelViewSet

from .models import MaintenanceRequest, MaintenanceUpdate, Vendor
from .serializers import (
    MAX_PHOTOS,
    AssignSerializer,
    CancelSerializer,
    CompleteSerializer,
    MaintenancePhotoSerializer,
    MaintenanceRequestDetailSerializer,
    MaintenanceRequestSerializer,
    MaintenanceUpdateSerializer,
    VendorSerializer,
)
from .services import assign_request, cancel_request, complete_request, start_request

# The board's last column shows jobs closed in the past week.
BOARD_DONE_WINDOW = timedelta(days=7)


class VendorViewSet(OrganizationScopedModelViewSet):
    serializer_class = VendorSerializer
    queryset = Vendor.objects.annotate(
        open_jobs=Count("requests", filter=Q(requests__status__in=MaintenanceRequest.OPEN_STATUSES))
    )
    filterset_fields = ["is_active", "trade"]
    search_fields = ["name", "trade", "contact_name", "phone_number"]
    ordering_fields = ["name", "created_at"]

    def perform_destroy(self, instance):
        # Vendors with job history are archived so past work keeps its record.
        if instance.requests.exists():
            instance.is_active = False
            instance.save(update_fields=["is_active", "updated_at"])
        else:
            instance.delete()


class MaintenanceFilter(filters.FilterSet):
    property = filters.UUIDFilter(field_name="property__public_id")
    unit = filters.UUIDFilter(field_name="unit__public_id")
    tenant = filters.UUIDFilter(field_name="tenant__public_id")
    vendor = filters.UUIDFilter(field_name="vendor__public_id")
    status = filters.MultipleChoiceFilter(choices=MaintenanceRequest.Status.choices)
    open = filters.BooleanFilter(method="filter_open")
    board = filters.BooleanFilter(method="filter_board")

    class Meta:
        model = MaintenanceRequest
        fields = ["property", "unit", "tenant", "vendor", "status", "priority", "category"]

    def filter_open(self, queryset, name, value):
        is_open = Q(status__in=MaintenanceRequest.OPEN_STATUSES)
        return queryset.filter(is_open) if value else queryset.exclude(is_open)

    def filter_board(self, queryset, name, value):
        if not value:
            return queryset
        since = timezone.now() - BOARD_DONE_WINDOW
        return queryset.filter(
            Q(status__in=MaintenanceRequest.OPEN_STATUSES)
            | Q(status=MaintenanceRequest.Status.COMPLETED, completed_at__gte=since)
        )


class MaintenanceRequestViewSet(OrganizationScopedModelViewSet):
    queryset = MaintenanceRequest.objects.select_related(
        "property", "unit", "tenant", "vendor", "invoice", "reported_by"
    ).annotate(photos_count=Count("photos", distinct=True))
    filterset_class = MaintenanceFilter
    search_fields = ["reference", "title", "unit__name", "property__name", "tenant__full_name"]
    ordering_fields = ["created_at", "priority", "scheduled_for", "completed_at"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    # Requests are closed or cancelled, never deleted.
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MaintenanceRequestDetailSerializer
        return MaintenanceRequestSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("updates__author", "photos")
        return queryset

    def detail_response(self, request_obj, status=200):
        self.action = "retrieve"
        instance = self.get_queryset().get(pk=request_obj.pk)
        serializer = MaintenanceRequestDetailSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(serializer.data, status=status)

    @action(detail=True, methods=["post"])
    def assign(self, request, public_id=None):
        job = self.get_object()
        serializer = AssignSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        job = assign_request(job, author=request.user, **serializer.validated_data)
        return self.detail_response(job)

    @action(detail=True, methods=["post"])
    def start(self, request, public_id=None):
        return self.detail_response(start_request(self.get_object(), author=request.user))

    @action(detail=True, methods=["post"])
    def complete(self, request, public_id=None):
        job = self.get_object()
        serializer = CompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = complete_request(job, author=request.user, **serializer.validated_data)
        return self.detail_response(job)

    @action(detail=True, methods=["post"])
    def cancel(self, request, public_id=None):
        job = self.get_object()
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = cancel_request(job, author=request.user, reason=serializer.validated_data["reason"])
        return self.detail_response(job)

    @action(detail=True, methods=["post"])
    def updates(self, request, public_id=None):
        job = self.get_object()
        serializer = MaintenanceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=job, author=request.user, kind=MaintenanceUpdate.Kind.COMMENT)
        return self.detail_response(job, status=201)

    @action(detail=True, methods=["post"])
    def photos(self, request, public_id=None):
        job = self.get_object()
        if job.photos.count() >= MAX_PHOTOS:
            raise ValidationError({"image": [f"A request can have up to {MAX_PHOTOS} photos."]})
        serializer = MaintenancePhotoSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(request=job, uploaded_by=request.user)
        return self.detail_response(job, status=201)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        requests = super().get_queryset()
        open_requests = requests.filter(status__in=MaintenanceRequest.OPEN_STATUSES)
        recent = requests.filter(
            status=MaintenanceRequest.Status.COMPLETED,
            completed_at__gte=timezone.now() - timedelta(days=90),
        )
        durations = [
            (completed - created).total_seconds()
            for created, completed in recent.values_list("created_at", "completed_at")
        ]
        average_days = round(sum(durations) / len(durations) / 86400, 1) if durations else None
        return Response(
            {
                "open": open_requests.count(),
                "urgent": open_requests.filter(priority=MaintenanceRequest.Priority.URGENT).count(),
                "unassigned": open_requests.filter(vendor__isnull=True).count(),
                "average_days_to_close": average_days,
                "by_status": {
                    row["status"]: row["count"]
                    for row in open_requests.values("status").annotate(count=Count("id"))
                },
            }
        )
