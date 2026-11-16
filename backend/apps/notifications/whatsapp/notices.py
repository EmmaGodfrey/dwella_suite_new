"""Approved-template messages about payment proofs, rechecked immediately before sending."""

import hashlib
import logging
import secrets
import time
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.audit.provider_credentials import credential
from apps.audit.runtime_settings import approved_whatsapp_templates, runtime_settings
from apps.billing.models import PaymentProof
from apps.common.provider_http import ProviderRejected, post_json
from apps.notifications.models import PhoneMessagingConsent
from apps.notifications.phone_messaging import normalize_phone, phone_allowed, whatsapp_ready
from apps.organizations.models import OrganizationMembership

from .access import actor_context, auth_stamp
from .models import WhatsAppBinding, WhatsAppProofNotice

logger = logging.getLogger(__name__)
ACTION_PREFIX = 'dw.'
# Order matches the template's quick-reply buttons in WhatsApp Manager.
REVIEW_VERBS = ('review', 'reject', 'ask')
ACTION_LIFETIME = timedelta(hours=24)
PURPOSES = {
    'review': ('dwella_payment_proof_review', PaymentProof.Status.SUBMITTED),
    'received': ('dwella_payment_received', PaymentProof.Status.CONFIRMED),
    'declined': ('dwella_payment_proof_declined', PaymentProof.Status.REJECTED),
    'question': ('dwella_payment_proof_question', PaymentProof.Status.NEEDS_INFORMATION),
}


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _recipients(proof, purpose):
    if purpose == 'review':
        users = OrganizationMembership.objects.filter(
            organization_id=proof.organization_id, role='landlord', is_active=True,
        ).values('user_id')
        role = 'landlord'
        query = WhatsAppBinding.objects.filter(user_id__in=users)
        # A reviewer who left or disconnected must not leave the proof unseen.
        reviewer = proof.organization.proof_reviewer
        if reviewer and reviewer.is_active and reviewer.role == 'landlord':
            chosen = query.filter(user_id=reviewer.user_id, revoked_at__isnull=True)
            if chosen.exists():
                query = chosen
    else:
        role = 'tenant'
        query = WhatsAppBinding.objects.filter(user_id=proof.tenant.user_id)
    return role, query.filter(revoked_at__isnull=True).order_by('pk')[:5]


def queue_proof_notice(proof, purpose):
    """Called inside the proof's own transaction; a failure here must not undo the proof."""
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED:
        return
    try:
        with transaction.atomic():
            role, bindings = _recipients(proof, purpose)
            for binding in bindings:
                WhatsAppProofNotice.objects.get_or_create(
                    binding=binding, proof=proof, revision=proof.revision, purpose=purpose,
                    defaults={'binding_generation': binding.generation, 'role': role,
                              'organization_id': proof.organization_id,
                              'expires_at': timezone.now() + ACTION_LIFETIME},
                )
    except DatabaseError as error:
        logger.warning('WhatsApp proof notice not queued class=%s', type(error).__name__)


def block(row, config):
    template, expected = PURPOSES[row.purpose]
    binding = row.binding
    if row.expires_at <= timezone.now():
        return 'expired'
    if row.proof.revision != row.revision or row.proof.status != expected:
        return 'proof_changed'
    if (binding.revoked_at or binding.generation != row.binding_generation or
            binding.auth_stamp != auth_stamp(binding.user)):
        return 'binding_changed'
    if not phone_allowed(binding.phone):
        return 'recipient_restricted'
    consent = PhoneMessagingConsent.objects.filter(
        channel='whatsapp', phone=binding.phone,
    ).first()
    # Unlike a reply inside a chat, this message is proactive and needs the opt-in.
    if not consent or not consent.allowed or consent.revoked_at:
        return 'recipient_opted_out'
    if f"{template}:{config['whatsapp_language']}" not in approved_whatsapp_templates():
        return 'template_required'
    ctx = actor_context(binding, row.organization_id)
    if ctx.role != row.role or (row.role == 'tenant' and row.proof.tenant_id not in ctx.tenant_ids):
        return 'access_changed'
    return ''


def _parameters(row):
    proof, invoice = row.proof, row.proof.invoice
    workspace = proof.organization
    amount = f'{workspace.currency} {proof.amount:,.2f}'
    tenant = proof.tenant.full_name
    if row.purpose == 'review':
        manager = row.binding.user.get_full_name() or 'there'
        values = (manager, tenant, amount, invoice.reference, proof.number)
    elif row.purpose == 'received':
        values = (tenant, workspace.name, amount, invoice.reference)
    else:
        values = (tenant, workspace.name, invoice.reference)
    # Meta refuses line breaks and runs of spaces inside template parameters.
    return [' '.join(str(value).split()) for value in values]


def payload(row, config, token=''):
    template, _ = PURPOSES[row.purpose]
    components = [{'type': 'body', 'parameters': [
        {'type': 'text', 'text': value} for value in _parameters(row)
    ]}]
    if token:
        components += [{
            'type': 'button', 'sub_type': 'quick_reply', 'index': str(index),
            'parameters': [{'type': 'payload', 'payload': f'{ACTION_PREFIX}{verb}.{token}'}],
        } for index, verb in enumerate(REVIEW_VERBS)]
    return {
        'messaging_product': 'whatsapp', 'to': row.binding.phone[1:],
        'biz_opaque_callback_data': str(row.public_id), 'type': 'template',
        'template': {'name': template, 'language': {'code': config['whatsapp_language']},
                     'components': components},
    }


def dispatch_proof_notices(limit=20, seconds=20):
    config = runtime_settings()
    if not settings.WHATSAPP_SELF_SERVICE_ENABLED or not whatsapp_ready(config):
        return 0
    # A process dying during network I/O leaves an uncertain outcome; never resend it.
    WhatsAppProofNotice.objects.filter(
        status='sending', claimed_at__lt=timezone.now() - timedelta(minutes=2),
    ).update(status='review', reason='send_outcome_unknown')
    ids = list(WhatsAppProofNotice.objects.filter(status='queued').order_by('pk').values_list(
        'pk', flat=True,
    )[:min(limit, 50)])
    started, accepted = time.monotonic(), 0
    related = ('binding__user', 'proof__invoice', 'proof__tenant', 'proof__organization')
    for pk in ids:
        if time.monotonic() - started >= seconds:
            break
        claim = uuid.uuid4()
        token = secrets.token_urlsafe(24)
        with transaction.atomic():
            row = WhatsAppProofNotice.objects.select_for_update(of=('self',)).select_related(
                *related,
            ).get(pk=pk)
            if row.status != 'queued':
                continue
            try:
                reason = block(row, config)
            except APIException:
                reason = 'access_denied'
            if reason:
                row.status, row.reason = 'cancelled', reason
                row.save(update_fields=['status', 'reason'])
                continue
            row.status, row.claim_token, row.claimed_at = 'sending', claim, timezone.now()
            row.token_hash = token_hash(token) if row.purpose == 'review' else ''
            row.save(update_fields=['status', 'claim_token', 'claimed_at', 'token_hash'])
        current = WhatsAppProofNotice.objects.filter(pk=pk, claim_token=claim, status='sending')
        try:
            result = post_json(
                f'https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/'
                f'{settings.WHATSAPP_PHONE_NUMBER_ID}/messages',
                payload(row, config, token if row.purpose == 'review' else ''),
                {'Authorization': f"Bearer {credential('WHATSAPP_ACCESS_TOKEN')}"},
            )
            provider_id = result['messages'][0]['id']
            if not isinstance(provider_id, str) or not provider_id or len(provider_id) > 160:
                raise ValueError('Invalid provider response.')
        except ProviderRejected as error:
            uncertain = error.code.startswith('http_5')
            current.update(status='review' if uncertain else 'failed',
                           reason='send_outcome_unknown' if uncertain else error.code)
        except Exception:
            current.update(status='review', reason='send_outcome_unknown')
        else:
            current.update(status='sent', provider_id=provider_id)
            WhatsAppProofNotice.objects.filter(
                pk=pk, claim_token=claim, provider_id='',
            ).update(provider_id=provider_id)
            accepted += 1
    return accepted


def apply_notice_status(data, stamp):
    query = Q(provider_id=data['id'])
    reference = data.get('biz_opaque_callback_data')
    if reference:
        try:
            query |= Q(public_id=uuid.UUID(reference), status__in=['sending', 'review'])
        except (ValueError, TypeError, AttributeError):
            return
    row = WhatsAppProofNotice.objects.select_for_update(of=('self',)).select_related(
        'binding',
    ).filter(query).first()
    recipient = normalize_phone('+' + str(data.get('recipient_id', '')))
    if not row or recipient != row.binding.phone:
        return
    ranks = {'sending': 0, 'review': 0, 'sent': 1, 'failed': 2, 'delivered': 3, 'read': 4}
    if ranks.get(data['status'], -1) < ranks.get(row.status, 99):
        return
    if row.provider_updated_at and stamp < row.provider_updated_at:
        return
    row.status, row.provider_id, row.provider_updated_at = data['status'], data['id'], stamp
    row.save(update_fields=['status', 'provider_id', 'provider_updated_at'])


def cleanup_notices(limit=200):
    ids = list(WhatsAppProofNotice.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=90),
    ).exclude(status='sending').order_by('pk').values_list('pk', flat=True)[:min(limit, 1000)])
    WhatsAppProofNotice.objects.filter(pk__in=ids).delete()
