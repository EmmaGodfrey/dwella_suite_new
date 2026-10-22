from rest_framework.routers import DefaultRouter

from .user_views import PlatformUserViewSet
from .views import SupportSessionViewSet

app_name = "audit"

router = DefaultRouter()
router.register("support-sessions", SupportSessionViewSet, basename="support-session")
router.register("users", PlatformUserViewSet, basename="platform-user")
urlpatterns = router.urls
