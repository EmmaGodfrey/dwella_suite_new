from rest_framework.routers import DefaultRouter

from .identity_views import IdentityReviewViewSet
from .user_views import PlatformUserViewSet
from .views import SupportSessionViewSet

app_name = "audit"

router = DefaultRouter()
router.register("support-sessions", SupportSessionViewSet, basename="support-session")
router.register("users", PlatformUserViewSet, basename="platform-user")
router.register("identity-verifications", IdentityReviewViewSet, basename="platform-identity")
urlpatterns = router.urls
