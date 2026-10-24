from rest_framework import serializers

from .catalog import Feature, Resource


class FeatureRuleSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    expires_at = serializers.DateTimeField(required=False, allow_null=True, default=None)

    def to_internal_value(self, data):
        if isinstance(data, dict) and set(data) - set(self.fields):
            raise serializers.ValidationError("Only enabled and expires_at may be supplied.")
        return super().to_internal_value(data)


class LimitField(serializers.IntegerField):
    def to_internal_value(self, data):
        if isinstance(data, bool):
            self.fail("invalid")
        return super().to_internal_value(data)


class AccessPolicyPatchSerializer(serializers.Serializer):
    feature_overrides = serializers.DictField(
        child=FeatureRuleSerializer(allow_null=True), required=False
    )
    limits = serializers.DictField(
        child=LimitField(min_value=0, max_value=2_147_483_647, allow_null=True),
        required=False,
    )

    def validate_feature_overrides(self, value):
        if set(value) - set(Feature.values):
            raise serializers.ValidationError("Choose registered feature keys only.")
        return {
            key: None
            if rule is None
            else {
                "enabled": rule["enabled"],
                "expires_at": rule["expires_at"].isoformat() if rule["expires_at"] else None,
            }
            for key, rule in value.items()
        }

    def validate_limits(self, value):
        if set(value) - set(Resource.values):
            raise serializers.ValidationError("Choose registered record limits only.")
        return value

    def validate(self, attrs):
        if set(self.initial_data) - set(self.fields):
            raise serializers.ValidationError("Only feature_overrides and limits may be changed.")
        if not attrs:
            raise serializers.ValidationError("Supply feature overrides or limits.")
        return attrs
