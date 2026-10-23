from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ContactViewSet,
    EnrollmentViewSet,
    MessageViewSet,
    OutreachSettingsView,
    SequenceViewSet,
    SummaryView,
    TemplateViewSet,
)

router = DefaultRouter()
router.register("contacts", ContactViewSet)
router.register("templates", TemplateViewSet)
router.register("sequences", SequenceViewSet)
router.register("enrollments", EnrollmentViewSet)
router.register("messages", MessageViewSet)
urlpatterns = [
    path("settings/", OutreachSettingsView.as_view()),
    path("summary/", SummaryView.as_view()),
] + router.urls
