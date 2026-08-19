from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PropertyOwnerViewSet, PropertyViewSet, UnitViewSet

app_name = "properties"

router = DefaultRouter()
router.register("owners", PropertyOwnerViewSet, basename="property-owner")
router.register("units", UnitViewSet, basename="unit")
router.register("", PropertyViewSet, basename="property")

urlpatterns = [path("", include(router.urls))]
