from datetime import timedelta

from rest_framework import serializers

from apps.billing.models import Payment


class ReportParameters(serializers.Serializer):
    property = serializers.UUIDField(required=False)
    export = serializers.ChoiceField(choices=["csv"], required=False)
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=25)

    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({
                key: "Unsupported report filter." for key in unknown
            })
        return super().to_internal_value(data)


class PeriodParameters(ReportParameters):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        today = self.context["today"]
        start = attrs.setdefault("date_from", today.replace(day=1))
        end = attrs.setdefault("date_to", today)
        if end < start:
            raise serializers.ValidationError({"date_to": "Choose a date on or after the start."})
        if end > today:
            raise serializers.ValidationError({"date_to": "Choose today or an earlier date."})
        if end - start > timedelta(days=365):
            raise serializers.ValidationError({"date_from": "Choose at most 366 days."})
        return attrs


class CollectionParameters(PeriodParameters):
    tenant = serializers.UUIDField(required=False)
    method = serializers.ChoiceField(choices=Payment.Method.choices, required=False)


class StatementParameters(PeriodParameters):
    tenant = serializers.UUIDField()
