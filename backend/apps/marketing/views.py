from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BetaApplication
from .serializers import BetaApplicationAdminSerializer, BetaApplicationSerializer


class BetaApplicationCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "beta_application"

    def post(self, request):
        serializer = BetaApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response(
            {
                "message": "Your beta application has been received.",
                "application_id": application.pk,
            },
            status=status.HTTP_201_CREATED,
        )


class BetaApplicationAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = BetaApplication.objects.all()
    serializer_class = BetaApplicationAdminSerializer
    permission_classes = [IsAdminUser]
    search_fields = ["name", "phone", "email", "town"]
    filterset_fields = ["status", "role"]
    ordering_fields = ["created_at", "name", "status"]
    ordering = ["-created_at"]
