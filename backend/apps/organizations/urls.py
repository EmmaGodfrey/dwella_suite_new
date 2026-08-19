from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OrganizationMembershipViewSet, OrganizationViewSet

app_name = "organizations"

router = DefaultRouter()
router.register("memberships", OrganizationMembershipViewSet, basename="organization-membership")
router.register("", OrganizationViewSet, basename="organization")

urlpatterns = [path("", include(router.urls))]
