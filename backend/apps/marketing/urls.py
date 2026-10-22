from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BetaApplicationAdminViewSet, BetaApplicationCreateView, unsubscribe

app_name = "marketing"

router = DefaultRouter()
router.register(
    "admin/beta-applications",
    BetaApplicationAdminViewSet,
    basename="admin-beta-application",
)

urlpatterns = [
    path("beta-applications/", BetaApplicationCreateView.as_view(), name="beta-application"),
    path("unsubscribe/<str:token>/", unsubscribe, name="beta-unsubscribe"),
    path("", include(router.urls)),
]
