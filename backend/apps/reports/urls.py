from django.urls import path

from .views import PortfolioReportView

app_name = "reports"

urlpatterns = [
    path("rent-roll/", PortfolioReportView.as_view(report="rent-roll"), name="rent-roll"),
    path("arrears/", PortfolioReportView.as_view(report="arrears"), name="arrears"),
]
