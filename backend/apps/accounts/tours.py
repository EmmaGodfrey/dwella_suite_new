from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.workspaces import resolve_workspace
from apps.organizations.models import Organization, OrganizationMembership

from .email_verification import NoStoreAccountView
from .models import GuidedTourState

# Append stable IDs when real modules ship. Never renumber/remove IDs to mark older work done.
TOURS = {
    "landlord": {
        "key": "manager_intro",
        "revision": 1,
        "steps": [
            {
                "id": "overview",
                "module": "dashboard",
                "title": "Your workspace at a glance",
                "body": "See your portfolio and what needs attention.",
                "path": "/dashboard",
                "target": "dashboard-overview",
            },
            {
                "id": "properties",
                "module": "properties",
                "title": "Your properties and units",
                "body": "Manage buildings, units and asking rent.",
                "path": "/properties",
                "target": "nav-properties",
            },
            {
                "id": "tenants",
                "module": "tenants",
                "title": "Your tenant records",
                "body": "Find contact details and link tenants to leases.",
                "path": "/tenants",
                "target": "nav-tenants",
            },
            {
                "id": "leases",
                "module": "leases",
                "title": "Your agreements and tenancy",
                "body": "Review lease terms, documents and signatures.",
                "path": "/leases",
                "target": "nav-leases",
            },
            {
                "id": "billing",
                "module": "billing",
                "title": "Invoices and recorded payments",
                "body": "Manage invoices, balances and receipts.",
                "path": "/billing",
                "target": "nav-billing",
            },
            {
                "id": "maintenance",
                "module": "maintenance",
                "title": "Requests and repairs",
                "body": "Follow maintenance requests through to completion.",
                "path": "/maintenance",
                "target": "nav-maintenance",
            },
        ],
    },
    "tenant": {
        "key": "tenant_intro",
        "revision": 1,
        "steps": [
            {
                "id": "profile",
                "module": "account",
                "title": "Your contact details",
                "body": "Keep your contact details up to date.",
                "path": "/profile",
                "target": "profile-details",
            },
            {
                "id": "security",
                "module": "account",
                "title": "Protect your account",
                "body": "Manage your authenticator and account security.",
                "path": "/security",
                "target": "security-settings",
            },
        ],
    },
}


def tour_definition(user, organization):
    if user.is_staff or user.is_superuser or not organization:
        return None
    membership = OrganizationMembership.objects.filter(
        user=user, organization=organization, organization__is_active=True, is_active=True
    ).first()
    definition = TOURS.get(membership.role) if membership else None
    if not definition:
        return None
    from apps.subscriptions.services import require_feature

    steps = []
    for step in definition["steps"]:
        if step.get("feature"):
            try:
                require_feature(organization, step["feature"])
            except PermissionDenied:
                continue
        steps.append(step)
    return {**definition, "steps": steps} if steps else None


def tour_snapshot(user, organization, state=None):
    definition = tour_definition(user, organization)
    if not definition:
        return {"available": False, "steps": []}
    if state is None:
        state = GuidedTourState.objects.filter(
            user=user, organization=organization, tour_key=definition["key"]
        ).first()
    ids = [step["id"] for step in definition["steps"]]
    complete = list(dict.fromkeys(state.completed_steps)) if state else []
    pending = [key for key in ids if key not in complete]
    status = state.status if state else "not_started"
    current = state.current_step if state and state.current_step in ids else (pending or ids)[0]
    return {
        "available": True,
        "tour_key": definition["key"],
        "revision": definition["revision"],
        "status": status,
        "current_step": current,
        "completed_steps": complete,
        "pending_steps": pending,
        "updates_available": status == "completed" and bool(pending),
        "steps": definition["steps"],
    }


class TourActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[
            "start",
            "resume",
            "next",
            "back",
            "pause",
            "skip",
            "finish",
            "replay",
            "new_steps",
        ]
    )
    step = serializers.CharField(max_length=64, required=False)


class GuidedTourView(NoStoreAccountView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return Response({"available": False, "steps": []})
        org = resolve_workspace(request)
        return Response(tour_snapshot(request.user, org))

    @transaction.atomic
    def patch(self, request):
        if request.user.is_staff or request.user.is_superuser:
            raise PermissionDenied("Support access cannot change a customer's tour progress.")
        org = resolve_workspace(request)
        if not org or not Organization.objects.filter(pk=org.pk, is_active=True).exists():
            raise PermissionDenied("A current workspace is required for this tour.")
        definition = tour_definition(request.user, org)
        if not definition:
            raise PermissionDenied("This tour is not available for this account.")
        data = TourActionSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        if tour_definition(request.user, org) is None:
            raise PermissionDenied("Workspace access changed. Refresh before continuing.")
        state, _ = GuidedTourState.objects.select_for_update().get_or_create(
            user=request.user, organization=org, tour_key=definition["key"]
        )
        ids = [step["id"] for step in definition["steps"]]
        action, step = data.validated_data["action"], data.validated_data.get("step")
        snapshot = tour_snapshot(request.user, org, state)
        current = snapshot["current_step"]
        if step is not None and step != current:
            raise ValidationError("The tour changed. Refresh before continuing.")
        completed = list(dict.fromkeys(state.completed_steps))
        if action in {"start", "replay", "new_steps"}:
            state.status = "in_progress"
            state.current_step = (
                (snapshot["pending_steps"] or ids)[0] if action == "new_steps" else ids[0]
            )
        elif action == "resume":
            state.status = "in_progress"
            state.current_step = current
        elif action in {"pause", "skip"}:
            state.status = "paused" if action == "pause" else "skipped"
            state.current_step = current
        elif action in {"next", "back", "finish"}:
            if state.status not in {"in_progress", "paused"}:
                raise ValidationError("Start or resume the tour first.")
            index = ids.index(current)
            if action == "back":
                state.current_step = ids[max(0, index - 1)]
                state.status = "in_progress"
            else:
                if current not in completed:
                    completed.append(current)
                if action == "finish" and (
                    index != len(ids) - 1 or any(key not in completed for key in ids)
                ):
                    raise ValidationError("Finish the available steps before completing the tour.")
                state.current_step = ids[min(len(ids) - 1, index + 1)]
                state.status = (
                    "completed"
                    if index == len(ids) - 1 and all(key in completed for key in ids)
                    else "in_progress"
                )
        state.completed_steps = completed
        state.save()
        return Response(tour_snapshot(request.user, org, state))
