from rest_framework.routers import DefaultRouter

from .views import SupportSessionViewSet

app_name = "audit"

router = DefaultRouter()
router.register("support-sessions", SupportSessionViewSet, basename="support-session")
urlpatterns = router.urls
