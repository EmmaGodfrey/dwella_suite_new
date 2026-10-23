from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.private_media import deny_public_identity_document


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"status": "ok", "service": "Dwella Suite API"})


urlpatterns = [
    path("api/v1/platform/outreach/", include("apps.outreach.urls")),
    path("api/v1/platform/", include("apps.audit.urls")),
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/assistant/", include("apps.assistant.urls")),
    path("api/v1/organizations/", include("apps.organizations.urls")),
    path("api/v1/properties/", include("apps.properties.urls")),
    path("api/v1/tenants/", include("apps.tenants.urls")),
    path("api/v1/leases/", include("apps.leases.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/maintenance/", include("apps.maintenance.urls")),
    path("api/v1/integrations/", include("apps.integrations.urls")),
    path("api/v1/marketing/", include("apps.marketing.urls")),
]

if settings.DEBUG:
    urlpatterns += [path(
        f"{settings.MEDIA_URL.lstrip('/')}profiles/verification_documents/<path:filename>",
        deny_public_identity_document,
    )]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
