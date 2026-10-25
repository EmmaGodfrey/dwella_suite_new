from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsPlatformAdmin

from .services import scheduler_status


class SchedulerStatusView(APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        return Response(scheduler_status())
