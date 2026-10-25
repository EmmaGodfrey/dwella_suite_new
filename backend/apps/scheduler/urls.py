from django.urls import path

from .views import SchedulerStatusView

app_name = "scheduler"

urlpatterns = [path("status/", SchedulerStatusView.as_view(), name="status")]
