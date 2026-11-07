import re

from django.db.models import Q
from rest_framework import serializers

from apps.accounts.security import normalize_email
from apps.common.serializers import PublicIdModelSerializer

from .models import (
    Contact,
    Enrollment,
    OutreachMessage,
    OutreachSettings,
    Sequence,
    SequenceStep,
    Suppression,
    Template,
)
from .rendering import validate_merge_fields


class ContactSerializer(PublicIdModelSerializer):
    suppressed = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "first_name",
            "salutation",
            "email",
            "phone",
            "whatsapp",
            "organization",
            "title",
            "segment",
            "platform",
            "handle",
            "profile_url",
            "audience_size",
            "town",
            "notes",
            "tags",
            "status",
            "source",
            "owner_id",
            "beta_application_id",
            "last_contacted_at",
            "replied_at",
            "created_at",
            "suppressed",
        ]
        read_only_fields = [
            "status",
            "owner_id",
            "beta_application_id",
            "last_contacted_at",
            "replied_at",
            "created_at",
        ]

    def get_suppressed(self, obj):
        if obj.status in ("do_not_contact", "bounced"):
            return True
        if not obj.email:
            return False
        if hasattr(obj, "has_suppression"):
            return obj.has_suppression
        return Suppression.objects.filter(email__iexact=obj.email).exists()

    def validate_email(self, value):
        value = normalize_email(value) if value else ""
        query = Contact.objects.filter(email__iexact=value).exclude(email="")
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("This email is already in your contacts.")
        return value

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Enter a contact name.")
        return value.strip()

    def validate_tags(self, value):
        if (
            not isinstance(value, list)
            or len(value) > 20
            or any(not isinstance(t, str) or not 1 <= len(t) <= 50 for t in value)
        ):
            raise serializers.ValidationError("Use up to 20 text tags, each 1–50 characters.")
        return value

    def validate(self, data):
        for field in ("phone", "whatsapp"):
            if data.get(field) and not re.fullmatch(r"\+?[\d\s()-]{7,32}", data[field]):
                raise serializers.ValidationError({field: "Enter a valid international number."})
        return data


class TemplateSerializer(PublicIdModelSerializer):
    class Meta:
        model = Template
        fields = [
            "id",
            "name",
            "segment",
            "subject",
            "body",
            "whatsapp_body",
            "is_follow_up",
            "active",
            "version",
        ]
        read_only_fields = ["version"]

    def validate(self, data):
        for key in ("subject", "body", "whatsapp_body"):
            if key in data:
                try:
                    validate_merge_fields(data[key])
                except serializers.ValidationError as error:
                    raise serializers.ValidationError({key: error.detail}) from error
        if any(c in data.get("subject", "") for c in "\r\n"):
            raise serializers.ValidationError({"subject": "Use a single subject line."})
        return data


class StepSerializer(serializers.ModelSerializer):
    template = serializers.SlugRelatedField(slug_field="public_id", queryset=Template.objects.all())
    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = SequenceStep
        fields = ["order", "template", "template_name", "wait_days", "only_if_no_reply"]
        read_only_fields = ["only_if_no_reply"]
        extra_kwargs = {"order": {"max_value": 19}, "wait_days": {"max_value": 365}}


class SequenceSerializer(PublicIdModelSerializer):
    steps = StepSerializer(many=True)

    class Meta:
        model = Sequence
        fields = ["id", "name", "description", "active", "steps"]

    def validate_steps(self, steps):
        if not 1 <= len(steps) <= 20 or sorted(s["order"] for s in steps) != list(
            range(len(steps))
        ):
            raise serializers.ValidationError("Use 1–20 steps numbered consecutively from zero.")
        if any(not s["template"].active for s in steps):
            raise serializers.ValidationError("Every step needs an active template.")
        return steps

    def create(self, validated_data):
        steps = validated_data.pop("steps")
        obj = super().create(validated_data)
        for step in steps:
            SequenceStep.objects.create(sequence=obj, **step)
        return obj

    def update(self, instance, validated_data):
        steps = validated_data.pop("steps", None)
        if steps is not None:
            if instance.enrollment_set.filter(
                Q(approved_at__isnull=False) | Q(messages__isnull=False)
            ).exists():
                raise serializers.ValidationError(
                    {"steps": "This sequence has approved recipients. Create a new sequence."},
                )
            instance.steps.all().delete()
            for step in steps:
                SequenceStep.objects.create(sequence=instance, **step)
        return super().update(instance, validated_data)


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutreachSettings
        fields = [
            "sender_name",
            "sender_first_name",
            "signature",
            "signature_short",
            "offer",
            "daily_cap",
            "send_from_hour",
            "send_until_hour",
            "paused",
        ]
        extra_kwargs = {
            "daily_cap": {"min_value": 1, "max_value": 25},
            "send_from_hour": {"min_value": 8, "max_value": 16},
            "send_until_hour": {"min_value": 9, "max_value": 17},
        }

    def validate(self, data):
        start = data.get("send_from_hour", getattr(self.instance, "send_from_hour", 8))
        end = data.get("send_until_hour", getattr(self.instance, "send_until_hour", 17))
        if start >= end:
            raise serializers.ValidationError({"send_until_hour": "End must follow start."})
        return data


class MessageSerializer(PublicIdModelSerializer):
    enrollment_status = serializers.CharField(source="enrollment.status", read_only=True)
    contact_id = serializers.UUIDField(source="enrollment.contact.public_id", read_only=True)
    contact_name = serializers.CharField(source="enrollment.contact.name", read_only=True)

    class Meta:
        model = OutreachMessage
        fields = [
            "id",
            "contact_id",
            "contact_name",
            "step",
            "subject",
            "body",
            "recipient",
            "status",
            "enrollment_status",
            "sent_at",
            "error",
            "created_at",
        ]


class EnrollmentSerializer(PublicIdModelSerializer):
    review = serializers.SerializerMethodField()

    def get_review(self, obj):
        from .services import review_snapshot

        if obj.status != "pending_review":
            return None
        try:
            return {"ready": True, **review_snapshot(obj)}
        except serializers.ValidationError as error:
            return {"ready": False, "errors": error.detail}

    contact = serializers.SlugRelatedField(slug_field="public_id", queryset=Contact.objects.all())
    sequence = serializers.SlugRelatedField(slug_field="public_id", queryset=Sequence.objects.all())
    contact_name = serializers.CharField(source="contact.name", read_only=True)
    contact_email = serializers.CharField(source="contact.email", read_only=True)
    sequence_name = serializers.CharField(source="sequence.name", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "contact",
            "contact_name",
            "contact_email",
            "sequence",
            "sequence_name",
            "status",
            "next_step",
            "next_send_at",
            "personal_line",
            "approved_at",
            "review",
        ]
        read_only_fields = ["status", "next_step", "next_send_at", "approved_at"]
