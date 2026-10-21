from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .onboarding import OnboardingView
from .views import OrganizationMembershipViewSet, OrganizationViewSet

app_name = "organizations"

router = DefaultRouter()
router.register("memberships", OrganizationMembershipViewSet, basename="organization-membership")
router.register("", OrganizationViewSet, basename="organization")

urlpatterns = [
    path("onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("", include(router.urls)),
]
