from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, OriginalViewSet

router = DefaultRouter()
router.register("versions", DocumentViewSet, basename="document")
router.register("originals", OriginalViewSet, basename="signed-original")
urlpatterns = router.urls
