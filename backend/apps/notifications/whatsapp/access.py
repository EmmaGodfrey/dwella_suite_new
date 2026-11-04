"""Explicit actor/workspace checks for workers, without constructing HTTP identities."""
import hashlib
import uuid
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.accounts.access_state import email_status
from apps.organizations.models import OrganizationMembership
from apps.subscriptions.catalog import Feature
from apps.subscriptions.services import require_feature
from apps.tenants.models import Tenant

from .models import WhatsAppBinding, WhatsAppConversation, WhatsAppReply


def auth_stamp(user):
    proof = email_status(user)['verified_at']
    return hashlib.sha256(
        f'{user.get_session_auth_hash()}:{user.email.strip().casefold()}:{proof}'.encode()
    ).hexdigest()


def require_actor(user):
    if (not user.is_active or user.is_staff or user.is_superuser
            or not email_status(user)['verified']):
        raise PermissionDenied('Reconnect WhatsApp from your verified Dwella account.')


def memberships(user):
    require_actor(user)
    return OrganizationMembership.objects.filter(
        user=user, is_active=True, organization__is_active=True,
        role__in=['landlord', 'tenant'],
    ).select_related('organization').order_by('organization_id')


@dataclass
class ActorContext:
    binding: WhatsAppBinding
    membership: OrganizationMembership
    tenant_ids: list

    @property
    def user(self):
        return self.binding.user

    @property
    def organization(self):
        return self.membership.organization

    @property
    def role(self):
        return self.membership.role

    def scope(self, queryset):
        query = queryset.filter(organization=self.organization, is_active=True)
        return query.filter(tenant_id__in=self.tenant_ids) if self.role == 'tenant' else query


def actor_context(binding, organization_id):
    require_actor(binding.user)
    if binding.revoked_at or binding.auth_stamp != auth_stamp(binding.user):
        raise PermissionDenied('Reconnect WhatsApp in Dwella settings.')
    member = memberships(binding.user).filter(organization_id=organization_id).first()
    if not member:
        raise PermissionDenied('This workspace is no longer available.')
    require_feature(member.organization, Feature.WHATSAPP_MESSAGES)
    tenant_ids = []
    if member.role == 'tenant':
        require_feature(member.organization, Feature.TENANT_PORTAL)
        tenant_ids = list(Tenant.objects.filter(
            organization=member.organization, user=binding.user, is_active=True,
        ).values_list('pk', flat=True))
        if not tenant_ids:
            raise PermissionDenied('This account is not linked to a tenancy.')
    return ActorContext(binding, member, tenant_ids)


@transaction.atomic
def revoke(phone=None, user=None):
    now = timezone.now()
    query = WhatsAppBinding.objects.filter(revoked_at__isnull=True)
    if phone is not None:
        query = query.filter(phone=phone)
    if user is not None:
        query = query.filter(user=user)
    ids = list(query.select_for_update().values_list('pk', flat=True))
    if not ids:
        return
    WhatsAppBinding.objects.filter(pk__in=ids).update(revoked_at=now, generation=uuid.uuid4())
    WhatsAppConversation.objects.filter(binding_id__in=ids).update(
        draft={}, expires_at=now, generation=uuid.uuid4(), organization=None, role='',
    )
    WhatsAppReply.objects.filter(binding_id__in=ids, status='queued').update(
        status='cancelled', reason='binding_revoked',
    )


@transaction.atomic
def bind(user, phone):
    require_actor(user)
    linked = Tenant.objects.filter(user=user, organization_id=OuterRef('organization_id'),
                                   is_active=True)
    if not memberships(user).annotate(linked=Exists(linked)).filter(
        Q(role='landlord') | Q(linked=True),
    ).exists():
        raise PermissionDenied('This account is not linked to a tenancy.')
    if WhatsAppBinding.objects.filter(phone=phone, revoked_at__isnull=True).exclude(
        user=user,
    ).exists():
        raise PermissionDenied('This number cannot be connected. Contact support.')
    revoke(user=user)
    binding, _ = WhatsAppBinding.objects.update_or_create(
        user=user, defaults={'phone': phone, 'generation': uuid.uuid4(),
                             'auth_stamp': auth_stamp(user), 'verified_at': timezone.now(),
                             'revoked_at': None},
    )
    return binding
