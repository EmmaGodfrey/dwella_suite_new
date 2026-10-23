from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import IdentityVerification
from apps.billing.models import Payment
from apps.common.permissions import IsPlatformAdmin
from apps.marketing.models import BetaApplication
from apps.organizations.models import Organization

from .models import SupportSession


class PlatformDashboardView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        now = timezone.now()
        today = timezone.localdate(now)
        return Response({
            "workspaces": Organization.objects.aggregate(
                active=Count("pk", filter=Q(is_active=True)),
                suspended=Count("pk", filter=Q(is_active=False)),
                new_this_week=Count("pk", filter=Q(created_at__gte=now - timedelta(days=7))),
            ),
            "users": get_user_model().objects.aggregate(
                total=Count("pk"), active=Count("pk", filter=Q(is_active=True)),
            ),
            "beta_signups": list(BetaApplication.objects.order_by().values("status").annotate(
                count=Count("pk"),
            ).order_by("status")),
            "open_support_sessions": SupportSession.objects.filter(
                ended_at__isnull=True, expires_at__gt=now, organization__is_active=True,
            ).count(),
            "pending_identity_checks": IdentityVerification.objects.filter(
                status="pending",
            ).count(),
            "collections_this_month": format(Payment.objects.filter(
                reversed_at__isnull=True, paid_on__gte=today.replace(day=1), paid_on__lte=today,
            ).aggregate(amount=Sum("amount"))["amount"] or 0, ".2f"),
        })
