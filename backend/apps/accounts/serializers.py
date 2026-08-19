from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from apps.organizations.serializers import OrganizationMembershipSerializer

User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    memberships = OrganizationMembershipSerializer(
        source="organization_memberships",
        many=True,
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "memberships",
        ]
        read_only_fields = ["id", "is_staff", "is_active", "memberships"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower()
        password = attrs["password"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Invalid email or password.") from exc

        authenticated_user = authenticate(
            request=self.context.get("request"),
            username=user.get_username(),
            password=password,
        )

        if authenticated_user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not authenticated_user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        attrs["user"] = authenticated_user
        return attrs
