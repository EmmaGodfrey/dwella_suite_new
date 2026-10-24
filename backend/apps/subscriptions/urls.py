from django.urls import path

from .views import WorkspaceEntitlementsView

app_name = "subscriptions"

urlpatterns = [path("entitlements/", WorkspaceEntitlementsView.as_view(), name="entitlements")]
