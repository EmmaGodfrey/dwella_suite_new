"""The one guided way to report a direct payment and to review it on WhatsApp.

Tenants pick an invoice, answer fixed questions, review and confirm. Managers see the
facts and files, then decide. Every write goes through billing.proofs, the same code the
website uses. Nothing here contacts a provider: files are fetched and sent by the worker.
"""
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.models import AuditEvent
from apps.billing import proofs
from apps.billing.models import Invoice, PaymentProof, PaymentProofFile

from .access import actor_context
from .conversation import choice, invoice_snapshot, menu, response, website
from .media import keep
from .models import WhatsAppMedia, WhatsAppProofNotice
from .notices import REVIEW_VERBS, token_hash

DRAFT_LIFETIME = timedelta(hours=24)
MAX_LISTED = 9
FILE_REQUIRED = {'bank_transfer', 'mobile_money'}
DATE_FORMATS = ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d %b %Y', '%d %B %Y')
FAILED_FILE = ('A file could not be used. Please send a clear JPG, PNG or PDF under 8 MB, '
               'or tap Done to continue without it.')


def _money(ctx, value):
    return f'{ctx.organization.currency} {value:,.2f}'


def _first_error(error):
    detail = error.detail
    while isinstance(detail, list | dict):
        detail = next(iter(detail.values() if isinstance(detail, dict) else detail), '')
    return str(detail) or 'That could not be completed.'


def _audit(ctx, action, proof):
    AuditEvent.objects.create(
        actor=ctx.user, organization=ctx.organization, action=action,
        resource_type='billing.paymentproof', resource_id=str(proof.public_id),
        metadata={'channel': 'whatsapp', 'amount': str(proof.amount)},
    )


def _leave(ctx, conversation, note):
    conversation.draft = {}
    return menu(ctx, conversation, note)


def _button(ctx, conversation, title, action, target=''):
    return choice(conversation, title, action, target, member=ctx.membership)


def _cancel(ctx, conversation):
    return _button(ctx, conversation, 'Cancel', 'menu')


def _open_invoices(ctx):
    return ctx.scope(Invoice.objects.all()).filter(
        status__in=Invoice.UNPAID_STATUSES,
    ).order_by('due_date', 'pk')


def _invoice(ctx, draft):
    return _open_invoices(ctx).filter(public_id=draft.get('invoice')).first()


# Tenant: report a payment


def _keep_file(ctx, conversation, payload):
    """Returns a note for the tenant. The file itself is fetched later by the worker."""
    draft = conversation.draft
    files = draft.setdefault('files', [])
    media_id = payload.get('media_id')
    if not media_id:
        return 'That file could not be read. Please send it again.'
    if len(files) >= PaymentProof.MAX_FILES:
        return f'You can send up to {PaymentProof.MAX_FILES} files, so that one was not added.'
    files.append(keep(ctx.binding, media_id).pk)
    return 'File received.'


def start_report(ctx, conversation, attachment=None):
    conversation.draft = {'intent': 'payment_proof', 'files': []}
    draft = conversation.draft
    note = _keep_file(ctx, conversation, attachment) if attachment else ''
    waiting = ctx.scope(PaymentProof.objects.all()).filter(
        status=PaymentProof.Status.NEEDS_INFORMATION,
    ).order_by('-reviewed_at', '-pk').first()
    if waiting:
        draft.update(step='question', question=str(waiting.public_id))
        return _ask(ctx, conversation, note)
    return _choose_invoice(ctx, conversation, note)


def _choose_invoice(ctx, conversation, note=''):
    draft = conversation.draft
    rows = list(_open_invoices(ctx)[:2])
    if not rows:
        return _leave(ctx, conversation, 'You have no unpaid invoices to report a payment for.')
    if len(rows) == 1:
        draft.update(invoice=str(rows[0].public_id), step='amount')
    else:
        draft['step'] = 'invoice'
    return _ask(ctx, conversation, note)


def _ask(ctx, conversation, note=''):
    """Render the current step. Buttons are replaced each turn, so any step can be re-asked."""
    draft = conversation.draft
    step = draft['step']
    # Finding a reference or screenshot takes time, but the final Confirm stays short-lived.
    if step != 'review':
        conversation.expires_at = timezone.now() + DRAFT_LIFETIME
    lead = f'{note}\n' if note else ''
    if step == 'question':
        proof = ctx.scope(PaymentProof.objects.all()).filter(
            public_id=draft['question'], status=PaymentProof.Status.NEEDS_INFORMATION,
        ).first()
        if not proof:
            return _choose_invoice(ctx, conversation, note)
        return response(
            f'{lead}Your property manager asked about payment {proof.number}:\n'
            f'{proof.review_note[:500]}\n\nAnswer it, or report a different payment?', [
                _button(ctx, conversation, 'Answer question', 'proof_answer'),
                _button(ctx, conversation, 'New payment', 'proof_new'),
                _cancel(ctx, conversation),
            ])
    if step == 'invoice':
        rows = list(_open_invoices(ctx)[:MAX_LISTED])
        lines = '\n'.join(f'{r.reference}: {_money(ctx, r.balance)}' for r in rows)
        return response(f'{lead}Which invoice did you pay?\n{lines}', [
            *[_button(ctx, conversation, r.reference, 'proof_invoice', r.public_id) for r in rows],
            _cancel(ctx, conversation),
        ], {'invoices': invoice_snapshot(rows)})
    invoice = _invoice(ctx, draft)
    if not invoice:
        return _leave(ctx, conversation, 'That invoice no longer has a balance to pay.')
    guards = {'invoices': invoice_snapshot([invoice])}
    if step == 'amount':
        return response(
            f'{lead}{invoice.reference}: {_money(ctx, invoice.balance)} outstanding.\n'
            'How much did you pay?', [
                _button(ctx, conversation, 'Full balance', 'proof_full'),
                _button(ctx, conversation, 'Other amount', 'proof_other'),
                _cancel(ctx, conversation),
            ], guards)
    if step == 'amount_text':
        return response(f'{lead}Type the amount you paid, for example 1500. '
                        f'The most you can report is {_money(ctx, invoice.balance)}. '
                        'Send CANCEL to stop.', guards=guards)
    if step == 'method':
        return response(f'{lead}How did you pay?', [
            *[_button(ctx, conversation, label, 'proof_method', value)
              for value, label in PaymentProof.METHODS],
            _cancel(ctx, conversation),
        ])
    if step == 'date':
        return response(f'{lead}When did you pay? Send CANCEL to stop.', [
            _button(ctx, conversation, 'Today', 'proof_today'),
            _button(ctx, conversation, 'Yesterday', 'proof_yesterday'),
            _button(ctx, conversation, 'Other date', 'proof_other_date'),
        ])
    if step == 'date_text':
        return response(f'{lead}Type the date you paid, for example 03/11/2026 (day/month/year). '
                        'Send CANCEL to stop.')
    if step == 'reference':
        return response(f'{lead}Type the transaction reference from your payment message, '
                        'or tap Skip.', [
                            _button(ctx, conversation, 'Skip', 'proof_skip'),
                            _cancel(ctx, conversation),
                        ])
    if step == 'files':
        count = len(draft.get('files', []))
        need = ('Send your screenshot or PDF now.' if draft['method'] in FILE_REQUIRED
                else 'Send a photo or PDF if you have one, or tap Done.')
        return response(f'{lead}{need} Up to {PaymentProof.MAX_FILES} files. '
                        f'Received so far: {count}.', [
                            _button(ctx, conversation, 'Done', 'proof_done'),
                            _cancel(ctx, conversation),
                        ])
    method = dict(PaymentProof.METHODS)[draft['method']]
    return response(
        f'{lead}Please check this before it goes to your property manager:\n'
        f'Invoice: {invoice.reference}\nAmount: {_money(ctx, Decimal(draft["amount"]))}\n'
        f'Method: {method}\nPaid on: {draft["paid_on"]}\n'
        f'Reference: {draft.get("reference") or "None"}\n'
        f'Files: {len(draft.get("files", []))}\n\n'
        'Your balance does not change until they confirm the money arrived.', [
            _button(ctx, conversation, 'Confirm', 'proof_confirm'),
            _cancel(ctx, conversation),
        ], guards)


def _parse_amount(text):
    value = re.sub(r'^(zmw|k)\s*', '', text.strip().casefold()).replace(',', '')
    if not re.fullmatch(r'\d{1,10}(\.\d{1,2})?', value):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _parse_date(text):
    for pattern in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), pattern).date()
        except ValueError:
            continue
    return None


def _files_ready(ctx, conversation):
    """Returns a note when the tenant must stay on the files step, otherwise an empty string."""
    draft = conversation.draft
    rows = list(WhatsAppMedia.objects.filter(
        pk__in=draft.get('files', []), binding=ctx.binding,
    ).defer('content'))
    if any(row.status in {'queued', 'fetching'} for row in rows):
        return 'Still checking your file. Please tap Done again in about a minute.'
    failed = [row.pk for row in rows if row.status != 'ready']
    if failed:
        draft['files'] = [pk for pk in draft['files'] if pk not in failed]
        WhatsAppMedia.objects.filter(pk__in=failed).delete()
        return FAILED_FILE
    existing = PaymentProofFile.objects.filter(
        proof__public_id=draft.get('resubmit'), organization=ctx.organization,
    ).exists() if draft.get('resubmit') else False
    if draft['method'] in FILE_REQUIRED and not draft['files'] and not existing:
        return 'A screenshot or PDF is needed for this payment method.'
    return ''


def _submit(ctx, conversation):
    draft = conversation.draft
    invoice = _invoice(ctx, draft)
    if not invoice:
        return _leave(ctx, conversation, 'That invoice no longer has a balance to pay.')
    rows = list(WhatsAppMedia.objects.filter(
        pk__in=draft.get('files', []), binding=ctx.binding, status='ready',
    ))
    uploads = [SimpleUploadedFile(row.name, bytes(row.content)) for row in rows]
    facts = {'amount': Decimal(draft['amount']), 'method': draft['method'],
             'paid_on': datetime.fromisoformat(draft['paid_on']).date(),
             'reference': draft.get('reference', ''), 'uploads': uploads}
    try:
        if draft.get('resubmit'):
            proof = ctx.scope(PaymentProof.objects.all()).filter(
                public_id=draft['resubmit'],
            ).first()
            if not proof:
                return _leave(ctx, conversation, 'That payment is no longer available.')
            proof = proofs.resubmit(proof, user=ctx.user, **facts)
            _audit(ctx, 'payment_proof.resend', proof)
        else:
            proof = proofs.submit(invoice, user=ctx.user, channel='whatsapp', **facts)
            _audit(ctx, 'payment_proof.submitted', proof)
    except ValidationError as error:
        return _leave(ctx, conversation, _first_error(error))
    WhatsAppMedia.objects.filter(pk__in=[row.pk for row in rows]).delete()
    return _leave(ctx, conversation, f'Sent. Your reference is {proof.number}. '
                  'We will tell you when your property manager has checked it.')


def _report_turn(ctx, conversation, payload, selected):
    draft = conversation.draft
    step, action = draft['step'], selected['action'] if selected else ''
    text = payload.get('text', '').strip()
    if payload.get('type') == 'attachment':
        note = _keep_file(ctx, conversation, payload)
        if step == 'review':
            draft['step'] = 'files'
        return _ask(ctx, conversation, note)
    if step == 'question':
        if action == 'proof_answer':
            proof = ctx.scope(PaymentProof.objects.select_related('invoice')).filter(
                public_id=draft['question'], status=PaymentProof.Status.NEEDS_INFORMATION,
            ).first()
            if not proof:
                return _choose_invoice(ctx, conversation)
            draft.update(resubmit=str(proof.public_id), invoice=str(proof.invoice.public_id),
                         step='amount')
        elif action == 'proof_new':
            return _choose_invoice(ctx, conversation)
    elif step == 'invoice' and action == 'proof_invoice':
        draft.update(invoice=selected['target'], step='amount')
    elif step == 'amount' and action == 'proof_full':
        invoice = _invoice(ctx, draft)
        if not invoice:
            return _leave(ctx, conversation, 'That invoice no longer has a balance to pay.')
        draft.update(amount=str(invoice.balance), step='method')
    elif step == 'amount' and action == 'proof_other':
        draft['step'] = 'amount_text'
    elif step == 'amount_text':
        invoice = _invoice(ctx, draft)
        if not invoice:
            return _leave(ctx, conversation, 'That invoice no longer has a balance to pay.')
        amount = _parse_amount(text)
        if amount is None or amount <= 0 or amount > invoice.balance:
            return _ask(ctx, conversation, 'That amount could not be used.')
        draft.update(amount=str(amount), step='method')
    elif step == 'method' and action == 'proof_method':
        if selected['target'] not in proofs.ALLOWED_METHODS:
            return _ask(ctx, conversation)
        draft.update(method=selected['target'], step='date')
    elif step == 'date' and action in {'proof_today', 'proof_yesterday'}:
        days = 0 if action == 'proof_today' else 1
        paid_on = timezone.localdate() - timedelta(days=days)
        draft.update(paid_on=paid_on.isoformat(), step='reference')
    elif step == 'date' and action == 'proof_other_date':
        draft['step'] = 'date_text'
    elif step == 'date_text':
        paid_on = _parse_date(text)
        if not paid_on or paid_on > timezone.localdate():
            return _ask(ctx, conversation, 'That date could not be used.')
        draft.update(paid_on=paid_on.isoformat(), step='reference')
    elif step == 'reference' and action == 'proof_skip':
        draft.update(reference='', step='files')
    elif step == 'reference' and text and not selected:
        if len(text) > 80:
            return _ask(ctx, conversation, 'References can be up to 80 characters.')
        draft.update(reference=text, step='files')
    elif step == 'files' and action == 'proof_done':
        problem = _files_ready(ctx, conversation)
        if problem:
            return _ask(ctx, conversation, problem)
        draft['step'] = 'review'
    elif step == 'review' and action == 'proof_confirm':
        return _submit(ctx, conversation)
    return _ask(ctx, conversation)


# Manager: review a payment


def _proof_guard(proof):
    return {'proofs': [[str(proof.public_id), proof.status, proof.revision]]}


def _current_proof(ctx, draft):
    return PaymentProof.objects.select_related('invoice', 'tenant').filter(
        organization=ctx.organization, public_id=draft.get('proof'),
        revision=draft.get('revision'), status=PaymentProof.Status.SUBMITTED,
    ).first()


def _show_proof(ctx, conversation, proof, evidence=True, note=''):
    conversation.draft = {'intent': 'review_proof', 'step': 'view',
                          'proof': str(proof.public_id), 'revision': proof.revision}
    files = list(PaymentProofFile.objects.filter(proof=proof).order_by('created_at').values(
        'public_id', 'sha256',
    ))
    digests = {row['sha256'] for row in files}
    others = sorted(set(PaymentProofFile.objects.filter(
        organization=ctx.organization, sha256__in=digests,
    ).exclude(proof=proof).values_list('proof__number', flat=True)))[:3]
    warning = f'\nThe same file is also on: {", ".join(others)}.' if others else ''
    lead = f'{note}\n' if note else ''
    view = response(
        f'{lead}Payment proof {proof.number}\nTenant: {proof.tenant.full_name}\n'
        f'Invoice: {proof.invoice.reference} ({_money(ctx, proof.invoice.balance)} outstanding)\n'
        f'Amount: {_money(ctx, proof.amount)}\nMethod: {proof.get_method_display()}\n'
        f'Paid on: {proof.paid_on}\nReference: {proof.reference or "None"}\n'
        f'Files: {len(files)}{warning}\n\nConfirm only after checking the money arrived.', [
            _button(ctx, conversation, 'Confirm received', 'proof_received'),
            _button(ctx, conversation, 'Not received', 'proof_not_received'),
            _button(ctx, conversation, 'Ask for details', 'proof_ask'),
            _button(ctx, conversation, 'Back', 'menu'),
        ], _proof_guard(proof))
    if evidence and files:
        view['evidence'] = [str(row['public_id']) for row in files]
    return view


def _ask_note(ctx, conversation, proof, step):
    conversation.draft = {'intent': 'review_proof', 'step': step,
                          'proof': str(proof.public_id), 'revision': proof.revision}
    prompt = ('Why was it not received? Send a short reason for the tenant.' if step == 'reason'
              else 'What do you need from the tenant? Send your question.')
    return response(f'{proof.number}: {prompt} Send CANCEL to go back.',
                    guards=_proof_guard(proof))


def start_review(ctx, conversation):
    rows = list(PaymentProof.objects.filter(
        organization=ctx.organization, status=PaymentProof.Status.SUBMITTED,
    ).select_related('tenant').order_by('submitted_at', 'pk')[:MAX_LISTED])
    if not rows:
        return _leave(ctx, conversation, 'No payments are waiting for you to review.')
    conversation.draft = {'intent': 'review_proof', 'step': 'list'}
    lines = '\n'.join(f'{r.number}: {r.tenant.full_name}, {_money(ctx, r.amount)}' for r in rows)
    return response(f'Which payment do you want to review?\n{lines}', [
        *[_button(ctx, conversation, r.number, 'proof_pick', r.public_id) for r in rows],
        _button(ctx, conversation, 'Main menu', 'menu'),
    ], {'proofs': [[str(r.public_id), r.status, r.revision] for r in rows]})


def _review_turn(ctx, conversation, payload, selected):
    draft = conversation.draft
    action = selected['action'] if selected else ''
    if draft['step'] == 'list':
        if action != 'proof_pick':
            return start_review(ctx, conversation)
        draft.update(proof=selected['target'])
        draft['revision'] = PaymentProof.objects.filter(
            organization=ctx.organization, public_id=selected['target'],
        ).values_list('revision', flat=True).first()
    proof = _current_proof(ctx, draft)
    if not proof:
        return _leave(ctx, conversation, 'That payment has already been reviewed or has changed.')
    if draft['step'] == 'list':
        return _show_proof(ctx, conversation, proof)
    if draft['step'] == 'view':
        if action == 'proof_received':
            try:
                proof = proofs.confirm(proof, user=ctx.user)
            except ValidationError as error:
                return _leave(ctx, conversation, _first_error(error))
            _audit(ctx, 'payment_proof.confirmed', proof)
            return _leave(ctx, conversation, f'{proof.number} confirmed. Receipt '
                          f'{proof.payment.receipt_number} was recorded for '
                          f'{proof.tenant.full_name}.')
        if action == 'proof_not_received':
            return _ask_note(ctx, conversation, proof, 'reason')
        if action == 'proof_ask':
            return _ask_note(ctx, conversation, proof, 'question')
        return _show_proof(ctx, conversation, proof, evidence=False)
    text = payload.get('text', '').strip()
    if not text or len(text) > 500:
        return _ask_note(ctx, conversation, proof, draft['step'])
    ask = draft['step'] == 'question'
    try:
        proof = proofs.decline(proof, user=ctx.user, note=text, ask=ask)
    except ValidationError as error:
        return _leave(ctx, conversation, _first_error(error))
    _audit(ctx, f'payment_proof.{proof.status}', proof)
    outcome = 'Your question was sent to' if ask else 'Marked as not received. We told'
    return _leave(ctx, conversation, f'{proof.number}: {outcome} {proof.tenant.full_name}.')


class ProofAdapter:
    def start(self, ctx, conversation, intent, target):
        if intent == 'payment_proof':
            return start_report(ctx, conversation)
        if intent == 'review_proof':
            return start_review(ctx, conversation)
        return _leave(ctx, conversation, 'This is not on WhatsApp yet. You can do it in Dwella: '
                      + website('billing'))

    def start_attachment(self, ctx, conversation, payload):
        return start_report(ctx, conversation, payload)

    def handle(self, ctx, conversation, payload, selected):
        if conversation.draft['intent'] == 'payment_proof' and ctx.role == 'tenant':
            return _report_turn(ctx, conversation, payload, selected)
        if conversation.draft['intent'] == 'review_proof' and ctx.role == 'landlord':
            return _review_turn(ctx, conversation, payload, selected)
        return _leave(ctx, conversation, 'That option is not available for this account.')

    def handle_action(self, binding, conversation, token):
        """A template button can arrive hours later, with no conversation still open."""
        conversation.draft = {}
        _, verb, secret = (token.split('.', 2) + ['', ''])[:3]
        # Holding the token proves delivery, even when the send response itself was lost.
        notice = WhatsAppProofNotice.objects.filter(
            token_hash=token_hash(secret), binding=binding, purpose='review',
            binding_generation=binding.generation,
        ).select_related('proof__invoice', 'proof__tenant').first()
        gone = 'That button is no longer available. Send MENU to see what is waiting for you.'
        if not notice or verb not in REVIEW_VERBS:
            return response(gone)
        ctx = actor_context(binding, notice.organization_id)
        if ctx.role != 'landlord':
            return response(gone)
        conversation.organization, conversation.role = ctx.organization, ctx.role
        proof = notice.proof
        if proof.revision != notice.revision or proof.status != PaymentProof.Status.SUBMITTED:
            label = proof.get_status_display().lower()
            return menu(ctx, conversation, f'{proof.number} is now: {label}.')
        if notice.expires_at <= timezone.now():
            return menu(ctx, conversation, f'That button has expired. {proof.number} is still '
                        'waiting: choose Review payment proof.')
        if verb == 'reject':
            return _ask_note(ctx, conversation, proof, 'reason')
        if verb == 'ask':
            return _ask_note(ctx, conversation, proof, 'question')
        return _show_proof(ctx, conversation, proof)


ADAPTER = ProofAdapter()
