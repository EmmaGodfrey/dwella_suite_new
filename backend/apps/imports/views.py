from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from . import services


class ImportThrottle(UserRateThrottle):
    scope = "portfolio_import"
    rate = "30/hour"


class ImportActionsMixin:
    """`import-template/`, `import-preview/` and `import-confirm/` on a portfolio viewset."""

    importer_class = None
    import_actions = frozenset({"import_template", "import_preview", "import_confirm"})

    def get_permissions(self):
        # An import can create records across every property, so it stays with admins.
        if getattr(self, "action", None) in self.import_actions:
            from apps.common.permissions import CanManageOrganization

            return [CanManageOrganization()]
        return super().get_permissions()

    def get_throttles(self):
        throttles = super().get_throttles()
        if self.action in {"import_preview", "import_confirm"}:
            throttles = [*throttles, ImportThrottle()]
        return throttles

    def importer(self):
        if self.request.query_params.get("kind") == "tenancies":
            from .importers import TenantImporter
            from .tenancies import TenancyImporter

            if self.importer_class is not TenantImporter:
                from rest_framework.exceptions import ValidationError

                raise ValidationError("Use the tenant import for combined tenancies.")
            return TenancyImporter(self.get_organization())
        return self.importer_class(self.get_organization())

    @action(detail=False, methods=["get"], url_path="import-template")
    def import_template(self, request):
        return services.template_response(self.importer())

    @action(detail=False, methods=["post"], url_path="import-preview")
    def import_preview(self, request):
        response = Response(services.preview(self.importer(), request, request.data))
        response["Cache-Control"] = "private, no-store"
        return response

    @action(detail=False, methods=["post"], url_path="import-confirm")
    def import_confirm(self, request):
        created = services.confirm(self.importer(), request, request.data)
        return Response(
            {"created": len(created), "ids": [str(item.public_id) for item in created]},
            status=status.HTTP_201_CREATED,
        )
