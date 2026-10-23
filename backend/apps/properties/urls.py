from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PropertyDashboardSummaryView,
    PropertyViewSet,
    UnitViewSet,
)

app_name = "properties"

router = DefaultRouter()
router.register("units", UnitViewSet, basename="unit")
router.register("", PropertyViewSet, basename="property")

urlpatterns = [
    path("dashboard/", PropertyDashboardSummaryView.as_view(), name="dashboard-summary"),
    path("", include(router.urls)),
]
