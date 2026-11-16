from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import team
from .onboarding import OnboardingView
from .views import OrganizationMembershipViewSet, OrganizationViewSet

app_name = "organizations"

router = DefaultRouter()
router.register("memberships", OrganizationMembershipViewSet, basename="organization-membership")
router.register("", OrganizationViewSet, basename="organization")

urlpatterns = [
    path("onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("team/", team.TeamView.as_view(), name="team"),
    path("team/activity/", team.TeamActivityView.as_view(), name="team-activity"),
    path("team/invitations/", team.TeamInvitationsView.as_view(), name="team-invitations"),
    path(
        "team/invitations/<uuid:public_id>/revoke/",
        team.TeamInvitationRevokeView.as_view(),
        name="team-invitation-revoke",
    ),
    path("team/members/<uuid:public_id>/", team.TeamMemberView.as_view(), name="team-member"),
    path("team/cover/", team.CoverView.as_view(), name="team-cover"),
    path("team/cover/<uuid:public_id>/", team.CoverView.as_view(), name="team-cover-end"),
    path("", include(router.urls)),
]
