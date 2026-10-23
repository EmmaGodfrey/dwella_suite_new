from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.models import UserProfile
from apps.common.permissions import IsPlatformAdmin
from apps.organizations.services import create_workspace

from .services import record_event
from .user_actions import UserAccountActions
from .user_security_actions import DeliveryUnavailable, UserSecurityActions
from .user_serializers import CreateUserInput, PlatformUserSerializer, UserFilters, UserProfileInput
from .user_services import change_membership, lock_target, require_superuser, send_access_email

User = get_user_model()


class PlatformUserViewSet(
    UserAccountActions,
    UserSecurityActions,
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformUserSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    search_fields = ["first_name", "last_name", "email", "profile__phone_number"]

    def get_queryset(self):
        query = User.objects.select_related(
            "profile", "identity_verification", "two_factor_device",
        ).prefetch_related("organization_memberships__organization").order_by("-date_joined", "pk")
        filters = UserFilters(data=dict(self.request.query_params.items()))
        filters.is_valid(raise_exception=True)
        data = filters.validated_data
        for name, field in [("active", "is_active"), ("staff", "is_staff")]:
            if name in data:
                query = query.filter(**{field: data[name]})
        if "workspace" in data:
            query = query.filter(
                organization_memberships__organization__public_id=data["workspace"],
                organization_memberships__is_active=True,
            )
        if "role" in data:
            query = query.filter(
                organization_memberships__role=data["role"],
                organization_memberships__is_active=True,
            )
        if "two_factor" in data:
            confirmed = Q(two_factor_device__is_confirmed=True)
            query = query.filter(confirmed if data["two_factor"] else ~confirmed)
        if "identity_status" in data:
            status = data["identity_status"]
            condition = Q(identity_verification__status=status)
            if status == "not_submitted":
                condition |= Q(identity_verification__isnull=True)
            query = query.filter(condition)
        persona = data.get("persona")
        if persona == "platform_admin":
            query = query.filter(Q(is_staff=True) | Q(is_superuser=True))
        elif persona:
            query = query.filter(is_staff=False, is_superuser=False)
            active = Q(organization_memberships__is_active=True)
            if persona == "unassigned":
                query = query.exclude(active)
            elif persona == "tenant":
                query = query.filter(active, organization_memberships__role="tenant")
            else:
                query = query.filter(active).exclude(organization_memberships__role="tenant")
        return query.distinct()

    def get_throttles(self):
        self.throttle_scope = "platform_write" if self.request.method == "POST" else None
        return super().get_throttles()

    @transaction.atomic
    def create(self, request):
        serializer = CreateUserInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if data["account_type"] == "platform_admin":
            require_superuser(request)
        first, _, last = data["full_name"].partition(" ")
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data["email"], email=data["email"], first_name=first, last_name=last,
                    password=None, is_staff=data["account_type"] == "platform_admin",
                    is_superuser=data["account_type"] == "platform_admin",
                )
        except IntegrityError as exc:
            raise ValidationError({"email": "This email is already in use."}) from exc
        UserProfile.objects.create(user=user, phone_number=data.get("phone_number", ""))
        if data["account_type"] == "landlord":
            create_workspace(user, display_name=data["workspace_name"])
        elif data["account_type"] == "member":
            change_membership(request, user, data["organization"], data["role"])
        from smtplib import SMTPException

        try:
            send_access_email(user)
        except (SMTPException, OSError) as exc:
            raise DeliveryUnavailable() from exc
        record_event(request, "user.created", user, account_type=data["account_type"])
        return Response(self.get_serializer(user).data, status=201)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        target = self.get_object()
        user = lock_target(request, target.pk)
        serializer = UserProfileInput(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "full_name" in data:
            user.first_name, _, user.last_name = data["full_name"].partition(" ")
        if "email" in data:
            user.email = user.username = data["email"]
        try:
            with transaction.atomic():
                user.save(update_fields=["first_name", "last_name", "email", "username"])
        except IntegrityError as exc:
            raise ValidationError({"email": "This email is already in use."}) from exc
        if "phone_number" in data:
            UserProfile.objects.update_or_create(
                user=user, defaults={"phone_number": data["phone_number"]},
            )
        record_event(request, "user.updated", user, fields=list(data))
        return Response(self.get_serializer(self.get_queryset().get(pk=user.pk)).data)
