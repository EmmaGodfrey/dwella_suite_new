from django.urls import path

from .collections import CollectionsReportView
from .statements import TenantStatementView
from .views import PortfolioReportView

app_name = "reports"

urlpatterns = [
    path("collections/", CollectionsReportView.as_view(), name="collections"),
    path("tenant-statement/", TenantStatementView.as_view(), name="tenant-statement"),
    path("rent-roll/", PortfolioReportView.as_view(report="rent-roll"), name="rent-roll"),
    path("arrears/", PortfolioReportView.as_view(report="arrears"), name="arrears"),
]
