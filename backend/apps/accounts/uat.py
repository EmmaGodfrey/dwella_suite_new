"""A bounded, account-private checklist for participants in the existing TEST app."""
import csv
import hashlib
import io
import json
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import Http404, HttpResponse
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.common.permissions import IsPlatformAdmin
from apps.reports.common import csv_cell

from .access_state import require_verified_access
from .admin_mfa import require_enrollment
from .models import UatResult

CAMPAIGN = "alpha-2026-11-07"
_source = Path(__file__).with_name("uat_cases.json").read_bytes()
CASES = json.loads(_source)
BY_ID = {row["id"]: row for row in CASES}
VERSION = hashlib.sha256(_source).hexdigest()[:12]


class UatWriteThrottle(UserRateThrottle):
    scope = "uat_results"
    rate = "240/hour"


class UatExportThrottle(UserRateThrottle):
    scope = "uat_export"
    rate = "30/hour"


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UatResult
        fields = ["case_id", "status", "notes", "updated_at"]
        read_only_fields = fields


class ResultUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=UatResult.Status.choices, required=False)
    notes = serializers.CharField(max_length=2000, allow_blank=True, required=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - {"status", "notes"}:
            raise ValidationError({"non_field_errors": ["Send only a result and/or note."]})
        if not data:
            raise ValidationError({"non_field_errors": ["Choose a result or add a note."]})
        return super().to_internal_value(data)


class UatBaseView(APIView):
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if settings.APP_ENVIRONMENT != "test" or not settings.ALPHA_TEST_ENABLED:
            raise Http404
        if not request.user.is_active:
            raise PermissionDenied("This account is unavailable.")
        require_verified_access(request.user, request)
        require_enrollment(request, request.user)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "private, no-store"
        return response


class UatChecklistView(UatBaseView):
    def get(self, request):
        results = UatResult.objects.filter(
            user=request.user, campaign=CAMPAIGN, case_id__in=BY_ID,
        ).only("case_id", "status", "notes", "updated_at").order_by("case_id")
        return Response({
            "campaign": CAMPAIGN, "version": VERSION, "cases": CASES,
            "results": ResultSerializer(results, many=True).data,
            "can_export": request.user.is_staff or request.user.is_superuser,
        })


class UatResultView(UatBaseView):
    throttle_classes = [UatWriteThrottle]

    def patch(self, request, case_id):
        if request.user.is_staff or request.user.is_superuser:
            raise PermissionDenied("This checklist records participant flows only.")
        if case_id not in BY_ID:
            raise Http404
        serializer = ResultUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            row, _ = UatResult.objects.get_or_create(
                user=request.user, campaign=CAMPAIGN, case_id=case_id,
            )
            row = UatResult.objects.select_for_update().get(pk=row.pk)
            changed = []
            for field, value in serializer.validated_data.items():
                if getattr(row, field) != value:
                    setattr(row, field, value)
                    changed.append(field)
            if changed:
                row.user_agent = request.META.get("HTTP_USER_AGENT", "")[:256]
                row.save(update_fields=[*changed, "user_agent", "updated_at"])
        return Response(ResultSerializer(row).data)


class ExportFilterSerializer(serializers.Serializer):
    tester = serializers.IntegerField(min_value=1, required=False)
    email = serializers.EmailField(required=False)


class UatExportView(UatBaseView):
    permission_classes = [IsPlatformAdmin]
    throttle_classes = [UatExportThrottle]

    def get(self, request):
        serializer = ExportFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = UatResult.objects.filter(campaign=CAMPAIGN, case_id__in=BY_ID)
        if "tester" in serializer.validated_data:
            query = query.filter(user_id=serializer.validated_data["tester"])
        if "email" in serializer.validated_data:
            query = query.filter(user__email__iexact=serializer.validated_data["email"])
        if query.count() > 5000:
            raise ValidationError("Choose a tester email to export at most 5,000 results.")
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Tester", "Email", "Flow ID", "Module", "Flow", "Result",
                         "Note", "Browser", "Saved at", "Campaign", "Catalogue"])
        rows = query.order_by("user_id", "case_id").values_list(
            "user_id", "user__email", "case_id", "status", "notes", "user_agent", "updated_at",
        )
        for user_id, email, case_id, status, notes, agent, updated in rows.iterator(chunk_size=200):
            case = BY_ID[case_id]
            writer.writerow([csv_cell(value) for value in [
                user_id, email, case_id, case["module"], case["title"], status, notes,
                agent, updated.isoformat(), CAMPAIGN, VERSION,
            ]])
        response = HttpResponse(
            "\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="dwella-test-results.csv"'
        return response
