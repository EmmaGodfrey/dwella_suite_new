from django.urls import path
from rest_framework.routers import DefaultRouter

from .dashboard_views import PlatformDashboardView
from .event_views import AuditEventViewSet
from .identity_views import IdentityReviewViewSet
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
    path("dashboard/", PlatformDashboardView.as_view(), name="platform-dashboard"),
] + router.urls
