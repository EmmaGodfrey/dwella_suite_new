from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TenantViewSet

app_name = "tenants"

router = DefaultRouter()
router.register("", TenantViewSet, basename="tenant")

urlpatterns = [path("", include(router.urls))]
