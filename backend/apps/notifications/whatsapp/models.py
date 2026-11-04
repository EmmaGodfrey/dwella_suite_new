import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class WhatsAppBinding(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=16)
    generation = models.UUIDField(default=uuid.uuid4)
    auth_stamp = models.CharField(max_length=64)
    verified_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['phone'], condition=models.Q(revoked_at__isnull=True),
            name='wa_active_phone_binding',
        )]

    def __str__(self):
        return f'WhatsApp binding {self.pk}'


class WhatsAppInbound(models.Model):
    number_id = models.CharField(max_length=80)
    provider_id = models.CharField(max_length=160)
    phone = models.CharField(max_length=16, db_index=True)
    happened_at = models.DateTimeField()
    received_at = models.DateTimeField(default=timezone.now)
    payload = models.JSONField(default=dict)
    binding_generation = models.UUIDField(null=True)
    status = models.CharField(max_length=16, default='queued')
    reason = models.CharField(max_length=80, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=['number_id', 'provider_id'], name='wa_unique_inbound',
        )]
        indexes = [models.Index(fields=['status', 'available_at', 'id'], name='wa_inbox_due')]
        indexes += [models.Index(fields=['phone', 'received_at'], name='wa_phone_received'),
                    models.Index(fields=['received_at'], name='wa_inbox_retention')]

    def __str__(self):
        return f'WhatsApp inbound {self.pk}'


class WhatsAppConversation(models.Model):
    binding = models.OneToOneField(WhatsAppBinding, on_delete=models.CASCADE)
    organization = models.ForeignKey('organizations.Organization', null=True,
                                     on_delete=models.SET_NULL)
    role = models.CharField(max_length=20, blank=True)
    revision = models.PositiveIntegerField(default=0)
    generation = models.UUIDField(default=uuid.uuid4)
    last_event_at = models.DateTimeField(null=True)
    draft = models.JSONField(default=dict)
    choices = models.JSONField(default=dict)
    expires_at = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self):
        return f'WhatsApp conversation {self.pk}'


class WhatsAppReply(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True)
    inbound = models.OneToOneField(WhatsAppInbound, on_delete=models.CASCADE)
    binding = models.ForeignKey(WhatsAppBinding, null=True, on_delete=models.SET_NULL)
    binding_generation = models.UUIDField(null=True)
    conversation_revision = models.PositiveIntegerField(default=0)
    organization = models.ForeignKey('organizations.Organization', null=True,
                                     on_delete=models.SET_NULL)
    role = models.CharField(max_length=20, blank=True)
    view = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=16, default='queued')
    reason = models.CharField(max_length=80, blank=True)
    claimed_at = models.DateTimeField(null=True)
    claim_token = models.UUIDField(null=True)
    provider_id = models.CharField(max_length=160, blank=True, db_index=True)
    provider_updated_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [models.Index(fields=['status', 'created_at', 'id'], name='wa_reply_due')]

    def __str__(self):
        return f'WhatsApp reply {self.public_id}'


class WhatsAppMedia(models.Model):
    """A file sent during a draft, held only until the draft is submitted or abandoned."""

    binding = models.ForeignKey(WhatsAppBinding, on_delete=models.CASCADE)
    binding_generation = models.UUIDField()
    media_id = models.CharField(max_length=160)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=16, default='queued')
    reason = models.CharField(max_length=80, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)
    claimed_at = models.DateTimeField(null=True)
    content = models.BinaryField(null=True)
    content_type = models.CharField(max_length=40, blank=True)
    name = models.CharField(max_length=120, blank=True)

    class Meta:
        indexes = [models.Index(fields=['status', 'available_at', 'id'], name='wa_media_due')]

    def __str__(self):
        return f'WhatsApp media {self.pk}'
