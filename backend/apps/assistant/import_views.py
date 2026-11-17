from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.common.property_scope import property_scope, require_property_admin
from apps.imports import services
from apps.imports.importers import PropertyImporter, TenantImporter, UnitImporter

from .serializers import AssistantImportConfirmSerializer, AssistantImportPreviewSerializer
from .views import ACTION_AUTH, ACTION_EXTENSION, HandyActionView


class AssistantImportView(HandyActionView):
    import_kind = ""

    def importer(self):
        organization = self.get_organization()
        if self.import_kind == "properties":
            require_property_admin(self.request)
            return PropertyImporter(organization)
        if self.import_kind == "units":
            scope = property_scope(self.request)
            return UnitImporter(
                organization,
                allowed_property_ids=None if scope.everything else scope.ids,
            )
        return TenantImporter(organization, created_by=self.request.user)


class AssistantImportPreviewView(AssistantImportView):
    throttle_scope = "handy_agent_action"

    @extend_schema(
        operation_id="assistant_preview_import_{kind}",
        summary="Preview a bulk {kind} import",
        description=(
            "Validates up to 500 CSV rows without creating records. Review the row counts "
            "and errors with the user, then obtain their explicit approval before calling "
            "the matching confirm action. The preview token is private, short-lived, and "
            "bound to this user and workspace. Property imports require a property admin; "
            "unit imports are limited to assigned properties for managers."
        ),
        request=AssistantImportPreviewSerializer,
        responses={200: dict},
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        serializer = self.validated(AssistantImportPreviewSerializer)
        result = services.preview(self.importer(), request, serializer.validated_data)
        # Do not echo tenant names, phone numbers, addresses, or imported row data
        # into the provider conversation. The user can review their source CSV.
        rows = []
        for item in result["rows"]:
            safe = {"row": item["row"], "status": item["status"]}
            if item.get("errors"):
                safe["errors"] = item["errors"]
            if item.get("message"):
                safe["message"] = item["message"]
            rows.append(safe)
        response = Response(
            {
                "kind": self.import_kind,
                "counts": result["counts"],
                "rows": rows,
                "ignored_columns": result["ignored_columns"],
                "preview_token": result["preview_token"],
                "next_step": (
                    "Show this summary and ask the user to explicitly confirm before importing."
                ),
            }
        )
        response["Cache-Control"] = "private, no-store"
        return response


class AssistantImportConfirmView(AssistantImportView):
    @extend_schema(
        operation_id="assistant_confirm_import_{kind}",
        summary="Confirm a reviewed bulk {kind} import",
        description=(
            "Creates exactly the ready rows from a prior preview. Call only after the user "
            "has reviewed the preview summary and explicitly approved the import. Tokens are "
            "single-use, expire after 30 minutes, and are bound to the same actor/workspace. "
            "All rows commit together or none do. Property imports require a property admin."
        ),
        request=AssistantImportConfirmSerializer,
        responses={201: dict},
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )
    def post(self, request):
        self.validated(AssistantImportConfirmSerializer)
        # The elevated requirement is checked before idempotency lookup and again
        # by importer construction during execution.
        if self.import_kind == "properties":
            require_property_admin(request)

        def create():
            with transaction.atomic():
                records, receipt = services.confirm(
                    self.importer(), request, request.data, include_receipt=True
                )
                scope_ids = set()
                if self.import_kind == "properties":
                    scope_ids = {record.pk for record in records}
                elif self.import_kind == "units":
                    scope_ids = {record.property_id for record in records}
                elif not property_scope(request).everything:
                    if any(record.created_by_id != request.user.pk for record in records):
                        raise PermissionDenied("Imported tenants are outside your current scope.")
                return (
                    {
                        "kind": self.import_kind,
                        "created": len(records),
                        "ids": [str(record.public_id) for record in records],
                    },
                    receipt,
                    scope_ids,
                )

        return self.execute(f"{self.import_kind}_imported", create)


def bind_import_views(kind):
    """Create schema-distinct action classes for each supported import kind."""
    label = kind.replace("_", " ")

    def preview_post(self, request):
        return AssistantImportPreviewView.post(self, request)

    preview_post = extend_schema(
        operation_id=f"assistant_preview_import_{kind}",
        summary=f"Preview a bulk {label} import",
        description=(
            "Validates up to 500 CSV rows without creating records. Review the row counts "
            "and errors with the user, then obtain explicit approval before calling the "
            "matching confirm action. The preview token is private, short-lived, and "
            "bound to this user and workspace. Property imports require a property admin; "
            "unit imports are limited to assigned properties for managers."
        ),
        request=AssistantImportPreviewSerializer,
        responses={200: dict},
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )(preview_post)

    def confirm_post(self, request):
        return AssistantImportConfirmView.post(self, request)

    confirm_post = extend_schema(
        operation_id=f"assistant_confirm_import_{kind}",
        summary=f"Confirm a reviewed bulk {label} import",
        description=(
            "Creates exactly the ready rows from a prior preview. Call only after the user "
            "has reviewed the preview summary and explicitly approved the import. Tokens are "
            "single-use, expire after 30 minutes, and are bound to the same actor/workspace. "
            "All rows commit together or none do. Property imports require a property admin."
        ),
        request=AssistantImportConfirmSerializer,
        responses={201: dict},
        tags=["Assistant actions"],
        extensions=ACTION_EXTENSION,
        auth=ACTION_AUTH,
    )(confirm_post)

    preview = type(
        f"Preview{kind.title()}ImportView",
        (AssistantImportPreviewView,),
        {"import_kind": kind, "post": preview_post},
    )
    confirm = type(
        f"Confirm{kind.title()}ImportView",
        (AssistantImportConfirmView,),
        {"import_kind": kind, "post": confirm_post},
    )
    return preview, confirm


PreviewPropertiesImportView, ConfirmPropertiesImportView = bind_import_views("properties")
PreviewUnitsImportView, ConfirmUnitsImportView = bind_import_views("units")
PreviewTenantsImportView, ConfirmTenantsImportView = bind_import_views("tenants")
