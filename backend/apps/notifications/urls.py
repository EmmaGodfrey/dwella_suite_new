from django.urls import path

from .message_views import (
    ConfirmView,
    MessageDetailView,
    MessagesView,
    PlatformMessagesView,
    PreviewView,
    RecipientsView,
)
from .settings_views import (
    PlatformMessagingView,
    PreferenceView,
    ReminderSettingsView,
    WorkspaceSettingsView,
)
from .views import NotificationsView

app_name = "notifications"

urlpatterns = [
    path("message-previews/", PreviewView.as_view()),
    path("message-previews/<uuid:public_id>/confirm/", ConfirmView.as_view()),
    path("message-recipients/", RecipientsView.as_view()),
    path("messages/", MessagesView.as_view()),
    path("messages/<uuid:public_id>/", MessageDetailView.as_view()),
    path("platform-messages/", PlatformMessagesView.as_view()),
    path("", NotificationsView.as_view(), name="notifications"),
    path("preferences/", PreferenceView.as_view()),
    path("reminders/", ReminderSettingsView.as_view()),
    path("platform-settings/", PlatformMessagingView.as_view()),
    path("workspace-settings/", WorkspaceSettingsView.as_view()),
]
