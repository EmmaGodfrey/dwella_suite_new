from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LeaseViewSet

app_name = "leases"

router = DefaultRouter()
router.register("", LeaseViewSet, basename="lease")

urlpatterns = [path("", include(router.urls))]
