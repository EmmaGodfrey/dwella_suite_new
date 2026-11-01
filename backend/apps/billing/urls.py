from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import deposit_views as deposit
from .views import InvoiceViewSet, PaymentInstructionViewSet, PaymentViewSet

app_name = "billing"

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")
router.register(
    "payment-instructions", PaymentInstructionViewSet, basename="payment-instruction"
)

urlpatterns = [
    path("deposits/<uuid:public_id>/", deposit.DepositView.as_view()),
    path("deposits/<uuid:public_id>/request/", deposit.DepositRequestView.as_view()),
    path("deposits/<uuid:public_id>/opening/", deposit.DepositOpeningView.as_view()),
    path("deposits/<uuid:public_id>/deductions/", deposit.DepositDeductionCreateView.as_view()),
    path("deposits/<uuid:public_id>/refunds/", deposit.DepositRefundView.as_view()),
    path(
        "deposit-deductions/<uuid:public_id>/<str:decision>/",
        deposit.DeductionDecisionView.as_view(),
    ),
    path("", include(router.urls)),
]
