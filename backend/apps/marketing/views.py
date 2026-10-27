import logging

from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .emails import BetaEmailError, application_from_token, deliver, send_due_emails
from .models import BetaApplication, BetaEmail
from .serializers import (
    BetaApplicationAdminCreateSerializer,
    BetaApplicationAdminSerializer,
    BetaApplicationSerializer,
)

logger = logging.getLogger(__name__)
RECEIVED = "Your beta application has been received."


def send_welcome_after_commit(application):
    """Signing up must never fail because email is slow or down; the scheduler retries."""

    def send():
        try:
            send_due_emails([application])
        except Exception:
            logger.exception("Welcome email for application %s failed", application.pk)

    transaction.on_commit(send)


class BetaApplicationCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "beta_application"

    def post(self, request):
        serializer = BetaApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        existing = email and BetaApplication.objects.filter(email__iexact=email).first()
        if existing:
            # Same answer as a first signup: no second welcome, no hint the email is known.
            return Response(
                {"message": RECEIVED, "application_id": existing.pk},
                status=status.HTTP_201_CREATED,
            )
        application = serializer.save()
        send_welcome_after_commit(application)
        return Response(
            {"message": RECEIVED, "application_id": application.pk},
            status=status.HTTP_201_CREATED,
        )


class BetaApplicationAdminViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = BetaApplication.objects.select_related("account").prefetch_related("emails")
    serializer_class = BetaApplicationAdminSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["name", "phone", "email", "town"]
    filterset_fields = ["status", "source"]
    ordering_fields = ["created_at", "name", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        from datetime import date

        from django.db.models import Exists, OuterRef

        query = super().get_queryset()
        early = self.request.query_params.get("early_access")
        if early is not None:
            if early not in ("true", "false"):
                raise ValidationError({"early_access": "Use true or false."})
            access = BetaEmail.objects.filter(
                application_id=OuterRef("pk"),
                kind="access",
                sent_at__date__lt=date.fromisoformat(settings.BETA_OPEN_DATE),
            )
            query = query.annotate(has_early_access=Exists(access)).filter(
                has_early_access=early == "true",
            )
        return query

    def get_serializer_class(self):
        if self.action == "create":
            return BetaApplicationAdminCreateSerializer
        return super().get_serializer_class()

    @transaction.atomic
    def perform_create(self, serializer):
        send_welcome = serializer.validated_data.get("send_welcome", True)
        early = serializer.validated_data.get("give_early_access", False)
        application = serializer.save()
        if early:
            from apps.audit.services import record_event
            from apps.outreach.early_access import deliver_access

            record_event(self.request, "marketing.beta_early_access", application)
            deliver_access(application)
        elif send_welcome:
            send_welcome_after_commit(application)

    @action(detail=True, methods=["post"], url_path="send-access")
    def send_access(self, request, pk=None):
        """Create the account and email sign-in details now, before or after beta day.
        Sending again issues a fresh set-password link."""
        application = self.get_object()
        if application.status == BetaApplication.Status.DECLINED:
            raise ValidationError({"detail": "This signup is declined. Change its status first."})
        try:
            deliver(application, BetaEmail.Kind.ACCESS, resend=True)
        except BetaEmailError as error:
            raise ValidationError({"detail": str(error)}) from error
        except Exception as error:
            logger.exception("Access email for application %s failed", application.pk)
            raise ValidationError(
                {"detail": "The email could not be sent. Check the email settings and try again."}
            ) from error
        if application.status != BetaApplication.Status.ACCEPTED:
            application.status = BetaApplication.Status.ACCEPTED
            application.save(update_fields=["status", "updated_at"])
        application = self.get_queryset().get(pk=application.pk)
        return Response(self.get_serializer(application).data)

    @action(detail=False, methods=["get"], url_path="email-settings")
    def email_settings(self, request):
        return Response(
            {
                "enabled": settings.BETA_EMAILS_ENABLED,
                "beta_open_date": settings.BETA_OPEN_DATE,
            }
        )


@csrf_exempt  # The signed per-recipient token is the credential; supports one-click POST.
@require_http_methods(["GET", "POST"])
def unsubscribe(request, token):
    application = application_from_token(token)
    context = {"site_url": settings.MARKETING_SITE_URL.rstrip("/")}
    template = "marketing/unsubscribe.html"
    if application is None:
        return render(request, template, {**context, "state": "invalid"}, status=404)
    if request.method == "POST":
        if not application.unsubscribed_at:
            application.unsubscribed_at = timezone.now()
            application.save(update_fields=["unsubscribed_at", "updated_at"])
        return render(request, template, {**context, "state": "done"})
    state = "done" if application.unsubscribed_at else "confirm"
    return render(request, template, {**context, "state": state, "email": application.email})
