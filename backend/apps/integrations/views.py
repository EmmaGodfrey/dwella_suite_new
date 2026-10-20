from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import (
    CanManageOrganization,
    CanManagePortfolio,
    get_active_membership,
)

from . import smart_invoice
from .models import FiscalReceipt, SmartInvoiceSettings
from .serializers import SmartInvoiceSettingsSerializer, tax_categories
from .zra.client import VsdcError


def device_mode():
    return "simulated" if settings.ZRA_VSDC_CLIENT.endswith("FakeVsdcClient") else "live"


class SmartInvoiceSettingsView(APIView):
    """The workspace's ZRA Smart Invoice connection (one per workspace)."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [CanManagePortfolio()]
        return [CanManageOrganization()]

    def get_organization(self):
        return get_active_membership(self.request.user).organization

    def get_instance(self):
        return SmartInvoiceSettings.objects.filter(organization=self.get_organization()).first()

    def payload(self, instance):
        unsent = FiscalReceipt.objects.filter(
            organization=self.get_organization(),
            status__in=[FiscalReceipt.Status.PENDING, FiscalReceipt.Status.FAILED],
        )
        return {
            "configured": instance is not None,
            "device_mode": device_mode(),
            "settings": SmartInvoiceSettingsSerializer(instance).data if instance else None,
            "tax_categories": tax_categories(),
            "unsent_receipts": unsent.count(),
        }

    def get(self, request):
        return Response(self.payload(self.get_instance()))

    def put(self, request):
        instance = self.get_instance()
        serializer = SmartInvoiceSettingsSerializer(
            instance, data=request.data, partial=instance is not None
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(organization=self.get_organization())
        return Response(self.payload(instance))

    patch = put


class SmartInvoiceInitialiseView(SmartInvoiceSettingsView):
    """Connect the saved device to ZRA and turn Smart Invoice on."""

    def get_permissions(self):
        return [CanManageOrganization()]

    def post(self, request):
        instance = self.get_instance()
        if instance is None:
            raise ValidationError({"tpin": ["Save your TPIN and device details first."]})
        if instance.initialized_at:
            raise ValidationError({"device_serial": ["This device is already connected to ZRA."]})
        try:
            with transaction.atomic():
                smart_invoice.initialise_device(instance)
                instance.enabled = True
                instance.save(update_fields=["enabled", "updated_at"])
        except VsdcError as error:
            raise ValidationError(
                {"device_serial": [f"ZRA could not connect this device ({error.message})."]}
            ) from error
        return Response(self.payload(instance))
