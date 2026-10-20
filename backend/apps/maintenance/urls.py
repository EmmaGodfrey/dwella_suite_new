from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MaintenanceRequestViewSet, VendorViewSet

app_name = "maintenance"

router = DefaultRouter()
router.register("vendors", VendorViewSet, basename="vendor")
router.register("requests", MaintenanceRequestViewSet, basename="maintenance-request")

urlpatterns = [path("", include(router.urls))]
