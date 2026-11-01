from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvoiceViewSet, PaymentInstructionViewSet, PaymentViewSet

app_name = "billing"

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")
router.register(
    "payment-instructions", PaymentInstructionViewSet, basename="payment-instruction"
)

urlpatterns = [path("", include(router.urls))]
