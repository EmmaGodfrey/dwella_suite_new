from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.subscriptions.views import PlatformEntitlementsView

from .dashboard_views import PlatformDashboardView
from .event_views import AuditEventViewSet
from .identity_views import IdentityReviewViewSet
from .runtime_views import AssistantConnectionCheckView, RuntimeSettingsView
from .settings_views import PlatformSettingsView
from .user_views import PlatformUserViewSet
from .views import SupportSessionViewSet
from .workspace_views import PlatformWorkspaceViewSet

app_name = "audit"

router = DefaultRouter()
router.register("audit-events", AuditEventViewSet, basename="platform-audit-event")
router.register("support-sessions", SupportSessionViewSet, basename="support-session")
router.register("users", PlatformUserViewSet, basename="platform-user")
router.register("identity-verifications", IdentityReviewViewSet, basename="platform-identity")
router.register("workspaces", PlatformWorkspaceViewSet, basename="platform-workspace")
urlpatterns = [
    path("runtime-settings/", RuntimeSettingsView.as_view(), name="runtime-settings"),
    path(
        "runtime-settings/assistant-check/", AssistantConnectionCheckView.as_view(),
        name="assistant-connection-check",
    ),
    path(
        "workspaces/<uuid:public_id>/entitlements/",
        PlatformEntitlementsView.as_view(),
        name="workspace-entitlements",
    ),
    path("settings/", PlatformSettingsView.as_view(), name="platform-settings"),
    path("dashboard/", PlatformDashboardView.as_view(), name="platform-dashboard"),
] + router.urls
