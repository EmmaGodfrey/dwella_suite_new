from rest_framework import serializers

from .models import TwoFactorDevice
from .security import verify_totp


class TwoFactorRemovalSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)
    code = serializers.RegexField(r"^[0-9]{6}$", write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        device = (
            TwoFactorDevice.objects.select_for_update().filter(user=user, is_confirmed=True).first()
        )
        if (
            not user.is_active
            or not device
            or not user.check_password(attrs["password"])
            or not verify_totp(device.secret, attrs["code"])
        ):
            raise serializers.ValidationError("Check your password and authenticator code.")
        return attrs
