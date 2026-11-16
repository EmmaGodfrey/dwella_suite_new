"""Account preparation without creating portfolio records or moving money."""

from uuid import uuid4

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.audit.services import record_event
from apps.billing.models import PaymentInstruction
from apps.billing.serializers import PaymentInstructionSerializer
from apps.notifications.models import ReminderPreferences
from apps.notifications.settings_views import ReminderSerializer

from .models import Organization, OrganizationMembership


class BusinessSetupSerializer(serializers.Serializer):
    business_name = serializers.CharField(max_length=180)
    email = serializers.EmailField(max_length=254)
    phone_number = serializers.RegexField(r"^\+?[0-9 ()-]{7,40}$")
    address = serializers.CharField(max_length=2000)
    town = serializers.CharField(max_length=120)
    country = serializers.CharField(max_length=80)
    confirm_region = serializers.BooleanField()

    def validate_confirm_region(self, value):
        if not value:
            raise serializers.ValidationError("Confirm the currency and time zone.")
        return value


class PaymentSetupSerializer(serializers.Serializer):
    payment_methods = serializers.ListField(
        child=serializers.ChoiceField(choices=["bank", "mobile_money", "cash"]),
        allow_empty=False, max_length=3,
    )

    def validate_payment_methods(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Choose each payment method once.")
        return value


class BillingSetupSerializer(serializers.Serializer):
    auto_invoice = serializers.BooleanField()
    invoice_lead_days = serializers.IntegerField(min_value=0, max_value=28)
    reminders = ReminderSerializer()


def valid_instruction_kinds(org):
    """At most three saved instructions; validate with the authoritative serializer."""
    kinds = set()
    if org:
        for item in PaymentInstruction.objects.filter(organization=org, is_active=True)[:3]:
            serializer = PaymentInstructionSerializer(item, data={}, partial=True)
            if serializer.is_valid():
                kinds.add(item.kind)
            else:
                kinds.add("invalid")
    return kinds


def account_status(org):
    business = {
        "business_name": str(org) if org else "",
        "email": org.email if org else "",
        "phone_number": org.phone_number if org else "",
        "address": org.address if org else "",
        "town": org.town if org else "",
        "country": org.country if org else "Zambia",
        "confirm_region": bool(org and org.setup_business_reviewed),
    }
    business_valid = BusinessSetupSerializer(data=business).is_valid()
    methods = org.setup_payment_methods if org else []
    method_serializer = PaymentSetupSerializer(data={"payment_methods": methods})
    payments_valid = method_serializer.is_valid() and (
        set(methods) - {"cash"} == valid_instruction_kinds(org)
    )
    done = [
        bool(org and org.setup_business_reviewed and business_valid),
        bool(payments_valid),
        bool(org and org.setup_billing_reviewed),
    ]
    done.append(bool(all(done) and org and org.setup_confirmed))
    reminders = (
        ReminderPreferences.objects.filter(organization=org).first() if org else None
    ) or ReminderPreferences()
    return {
        "account_ready": all(done),
        "account_steps": [
            {"key": key, "label": label, "done": complete, "path": "/setup",
             "group": "account", "required": True}
            for (key, label), complete in zip([
                ("workspace", "Review business details"),
                ("payment_methods", "Choose how tenants pay"),
                ("billing_preferences", "Review billing and reminders"),
                ("account_review", "Confirm account setup"),
            ], done, strict=True)
        ],
        "business": business,
        "currency": org.currency if org else "ZMW",
        "timezone": org.timezone if org else "Africa/Lusaka",
        "payment_methods": methods,
        "billing": {
            "auto_invoice": org.auto_invoice if org else True,
            "invoice_lead_days": org.invoice_lead_days if org else 7,
            "reminders": ReminderSerializer(reminders).data,
        },
    }


def save_account_stage(request, stage, org):
    if not isinstance(stage, str):
        raise ValidationError({"stage": "Choose a valid setup stage."})
    serializer_class = {
        "business": BusinessSetupSerializer,
        "payments": PaymentSetupSerializer,
        "billing": BillingSetupSerializer,
        "complete": serializers.Serializer,
    }.get(stage)
    if serializer_class is None:
        raise ValidationError({"stage": "Choose a valid setup stage."})
    payload = {key: value for key, value in request.data.items() if key != "stage"}
    serializer = serializer_class(data=payload)
    # Never accept client-supplied workspace, readiness or authorization fields.
    unknown = set(payload) - set(serializer.fields)
    if unknown:
        raise ValidationError({key: "Unknown setup field." for key in unknown})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if not org and stage != "business":
        raise ValidationError({"stage": "Save your business details first."})
    if not org:
        org = Organization.objects.create(name=f"workspace-{uuid4().hex}")
        membership = OrganizationMembership.objects.create(
            organization=org, user=request.user, role=OrganizationMembership.Role.LANDLORD,
        )
        request._workspace_membership = (request.user.pk, membership)
        if hasattr(request._request, "_property_scope"):
            del request._request._property_scope
        request.organization = org
        request._request.organization = org
    if stage == "business":
        org.display_name = data.pop("business_name")
        data.pop("confirm_region")
        for key, value in data.items():
            setattr(org, key, value)
        org.setup_business_reviewed = True
    elif stage == "payments":
        methods = data["payment_methods"]
        if not set(methods) - {"cash"} <= valid_instruction_kinds(org):
            raise ValidationError({"payment_methods": (
                "Add complete payment details for every selected bank or mobile-money method."
            )})
        # Every printed instruction is an accepted method; do not silently discard
        # saved accounts when someone chooses cash only.
        saved_kinds = set(PaymentInstruction.objects.filter(
            organization=org, is_active=True,
        ).values_list("kind", flat=True))
        if not saved_kinds <= set(methods):
            raise ValidationError({"payment_methods": (
                "Select your saved payment methods, or remove their details first."
            )})
        org.setup_payment_methods = methods
    elif stage == "billing":
        org.auto_invoice = data["auto_invoice"]
        org.invoice_lead_days = data["invoice_lead_days"]
        preferences, _ = ReminderPreferences.objects.get_or_create(organization=org)
        preferences = ReminderPreferences.objects.select_for_update().get(pk=preferences.pk)
        reminder_serializer = ReminderSerializer(preferences, data=data["reminders"], partial=True)
        reminder_serializer.is_valid(raise_exception=True)
        reminder_serializer.save()
        org.setup_billing_reviewed = True
    elif stage == "complete":
        if not all(step["done"] for step in account_status(org)["account_steps"][:3]):
            raise ValidationError({
                "stage": "Finish the business, payment and billing steps first.",
            })
    org.setup_confirmed = stage == "complete"
    org.save()
    request.organization = org
    request._request.organization = org
    record_event(request, f"organizations.setup_{stage}_saved", org, org)
    return org
