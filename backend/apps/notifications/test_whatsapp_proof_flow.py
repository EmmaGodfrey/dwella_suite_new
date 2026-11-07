"""The guided payment-proof conversation, driven through signed webhooks and the worker."""
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.utils import timezone
from PIL import Image

from apps.audit.models import AuditEvent
from apps.billing import proofs
from apps.billing.models import Invoice, Payment, PaymentProof

from . import test_whatsapp as base
from .models import PhoneMessagingConsent
from .test_whatsapp import PHONE, callback, choose, linked, step
from .whatsapp.media import fetch_media
from .whatsapp.models import WhatsAppMedia, WhatsAppProofNotice, WhatsAppReply
from .whatsapp.notices import dispatch_proof_notices
from .whatsapp.transport import dispatch_replies
from .whatsapp.worker import process_inbox

pytestmark = pytest.mark.django_db
config = base.config
house = base.house
META = {'url': 'https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1',
        'mime_type': 'image/png', 'file_size': 100}


@pytest.fixture(autouse=True)
def approved(settings, config):
    settings.APPROVED_WHATSAPP_TEMPLATES = ['dwella_payment_proof_review:en']
    settings.WHATSAPP_TEMPLATE_LANGUAGE = 'en'


def session(house, role='tenant'):
    """Whether the first message opens the chooser or the menu, end on the main menu."""
    linked(house, role)
    reply = step()
    if reply.view['text'] == 'Choose your workspace.':
        reply = step(token=reply.view['options'][0]['id'])
    return reply


def tap(reply, title):
    return step(token=choose(reply, title))


def png():
    raw = BytesIO()
    Image.new('RGB', (40, 40), 'white').save(raw, format='PNG')
    return raw.getvalue()


def send_file(identity='wamid.file'):
    row = {'id': identity, 'from': PHONE[1:], 'type': 'image',
           'timestamp': str(int(timezone.now().timestamp())),
           'image': {'id': f'media-{identity}', 'mime_type': 'image/png'}}
    assert callback([row]).status_code == 200
    process_inbox()
    return WhatsAppReply.objects.latest('pk')


def fetch(content=None):
    with patch('apps.notifications.whatsapp.media.get_json', return_value=META), patch(
        'apps.notifications.whatsapp.media.get_bytes', return_value=content or png(),
    ):
        fetch_media()


def to_files_step(house, method='Mobile money'):
    menu = session(house)
    amount = tap(menu, 'I have already paid')
    methods = tap(amount, 'Full balance')
    tap(tap(methods, method), 'Today')
    return step('MP241101')


def press(verb_payload):
    row = {'id': f'wamid.{verb_payload[-12:]}', 'from': PHONE[1:], 'type': 'button',
           'timestamp': str(int(timezone.now().timestamp())),
           'button': {'payload': verb_payload, 'text': 'Button'}}
    assert callback([row]).status_code == 200
    process_inbox()
    return WhatsAppReply.objects.latest('pk')


def report(house, **extra):
    return proofs.submit(house['invoice'], user=house['tenant'], amount=Decimal('100'),
                         method='mobile_money', paid_on=timezone.localdate(), reference='MP1',
                         **extra)


def manager_buttons(house):
    """Connect the manager, deliver the template, and return its three button payloads."""
    linked(house, 'manager')
    PhoneMessagingConsent.objects.update(allowed=True)
    proof = report(house)
    with patch('apps.notifications.whatsapp.notices.post_json',
               return_value={'messages': [{'id': 'wamid.template'}]}) as post:
        assert dispatch_proof_notices() == 1
    components = post.call_args.args[1]['template']['components'][1:]
    return proof, [row['parameters'][0]['payload'] for row in components]


def test_tenant_reports_a_payment_step_by_step(house):
    files = to_files_step(house)
    assert 'Send your screenshot or PDF now' in files.view['text']
    send_file()
    fetch()
    review = step(token=choose(WhatsAppReply.objects.latest('pk'), 'Done'))
    assert 'Reference: MP241101' in review.view['text']
    assert 'Files: 1' in review.view['text']
    assert not PaymentProof.objects.exists()

    done = tap(review, 'Confirm')

    proof = PaymentProof.objects.get()
    assert (proof.channel, proof.method) == ('whatsapp', 'mobile_money')
    assert proof.reference == 'MP241101'
    assert proof.amount == house['invoice'].balance and proof.submitted_by == house['tenant']
    assert proof.number in done.view['text']
    assert proof.files.get().content_type == 'image/jpeg'
    assert not WhatsAppMedia.objects.exists()
    assert AuditEvent.objects.filter(action='payment_proof.submitted').exists()
    house['invoice'].refresh_from_db()
    assert house['invoice'].amount_paid == 0


def test_screenshot_sent_outside_requested_step_returns_safe_menu(house):
    session(house)
    reply = send_file()
    assert 'Choose I have already paid or Report a repair first' in reply.view['text']
    assert WhatsAppMedia.objects.count() == 0


def test_screenshot_before_choosing_a_workspace_is_not_imported_into_a_draft(house):
    from apps.organizations.models import Organization, OrganizationMembership
    from apps.tenants.models import Tenant

    other = Organization.objects.create(name='Second home')
    OrganizationMembership.objects.create(organization=other, user=house['tenant'], role='tenant')
    Tenant.objects.create(organization=other, user=house['tenant'], full_name='Second tenancy')
    linked(house)
    chooser = send_file()
    assert chooser.view['text'] == 'Choose your workspace.'
    first = next(row for row in chooser.view['options'] if row['title'] == 'WhatsApp workspace')

    reply = step(token=first['id'])

    assert 'How can Dwella help?' in reply.view['text']
    assert WhatsAppMedia.objects.count() == 0


def test_bank_and_mobile_money_need_a_file_but_cash_does_not(house):
    files = to_files_step(house)
    again = tap(files, 'Done')
    assert 'A screenshot or PDF is needed' in again.view['text']
    assert choose(again, 'Done')


def test_cash_can_be_reported_without_a_file(house):
    menu = session(house)
    methods = tap(tap(menu, 'I have already paid'), 'Full balance')
    reference = tap(tap(methods, 'Cash'), 'Yesterday')
    files = tap(reference, 'Skip')
    review = tap(files, 'Done')
    tap(review, 'Confirm')
    proof = PaymentProof.objects.get()
    assert (proof.method, proof.paid_on) == ('cash', timezone.localdate() - timedelta(days=1))


def test_done_waits_for_a_file_still_being_checked(house):
    to_files_step(house)
    reply = send_file()
    again = tap(reply, 'Done')
    assert 'Still checking your file' in again.view['text']


def test_unusable_file_is_dropped_and_explained(house):
    to_files_step(house)
    reply = send_file()
    fetch(b'not an image')
    again = tap(reply, 'Done')
    assert 'could not be used' in again.view['text']
    assert not WhatsAppMedia.objects.exists()


@pytest.mark.parametrize('typed', ['abc', '0', '-5', '99999999'])
def test_bad_amounts_are_asked_again(house, typed):
    menu = session(house)
    typing = tap(tap(menu, 'I have already paid'), 'Other amount')
    reply = step(typed)
    assert reply.view['text'].startswith('That amount could not be used.')
    assert typing.view['text'] in reply.view['text']


@pytest.mark.parametrize('typed', ['K100', 'ZMW 100.50', '1,00'])
def test_amount_formats_people_type(house, typed):
    menu = session(house)
    tap(tap(menu, 'I have already paid'), 'Other amount')
    assert 'How did you pay?' in step(typed).view['text']


def test_future_date_is_refused(house):
    menu = session(house)
    methods = tap(tap(menu, 'I have already paid'), 'Full balance')
    tap(tap(methods, 'Cash'), 'Other date')
    future = (timezone.localdate() + timedelta(days=2)).strftime('%d/%m/%Y')
    assert step(future).view['text'].startswith('That date could not be used.')


def test_typed_text_on_a_button_step_repeats_the_question(house):
    menu = session(house)
    tap(menu, 'I have already paid')
    assert 'How much did you pay?' in step('hello there').view['text']


def test_cancel_discards_the_draft_and_nothing_is_sent(house):
    to_files_step(house)
    send_file()
    reply = step('cancel')
    assert reply.view['text'].endswith('Cancelled. Nothing was sent.')
    assert not PaymentProof.objects.exists()
    with patch('apps.notifications.whatsapp.media.get_json') as lookup:
        fetch_media()
    lookup.assert_not_called()
    assert not WhatsAppMedia.objects.exists()


def test_invoice_paid_during_the_flow_is_not_reported(house):
    review = tap(tap(tap(tap(tap(session(house), 'I have already paid'), 'Full balance'),
                         'Cash'), 'Today'), 'Skip')
    review = tap(review, 'Done')
    Invoice.objects.filter(pk=house['invoice'].pk).update(status='paid')
    reply = tap(review, 'Confirm')
    assert 'no longer has a balance' in reply.view['text']
    assert not PaymentProof.objects.exists()


def second_invoice(house):
    second = Invoice.objects.get(pk=house['invoice'].pk)
    second.pk = None
    second.public_id = uuid4()
    second.reference = 'INV-SECOND'
    second.period_start = second.period_start - timedelta(days=31)
    second.save()
    return second


def test_pay_rent_links_to_the_only_unpaid_invoice_and_changes_nothing(house):
    invoice = house['invoice']
    reply = tap(session(house), 'Pay rent')
    assert f'billing/invoices/{invoice.public_id}' in reply.view['text']
    assert invoice.reference in reply.view['text']
    invoice.refresh_from_db()
    assert invoice.amount_paid == 0 and not Payment.objects.exists()
    # Someone who already paid directly is one tap from reporting it.
    assert 'How much did you pay?' in tap(reply, 'I have already paid').view['text']


def test_pay_rent_asks_which_invoice_when_there_are_several(house):
    second = second_invoice(house)
    choosing = tap(session(house), 'Pay rent')
    assert 'Which invoice do you want to pay?' in choosing.view['text']
    reply = tap(choosing, 'INV-SECOND')
    assert f'billing/invoices/{second.public_id}' in reply.view['text']


def test_pay_rent_with_nothing_owed_says_so(house):
    Invoice.objects.filter(pk=house['invoice'].pk).update(status='paid')
    reply = tap(session(house), 'Pay rent')
    assert 'You have nothing to pay right now.' in reply.view['text']


def test_pay_rent_for_an_invoice_paid_meanwhile_links_to_nothing(house):
    second = second_invoice(house)
    choosing = tap(session(house), 'Pay rent')
    Invoice.objects.filter(pk=second.pk).update(status='paid')
    reply = tap(choosing, 'INV-SECOND')
    assert 'no longer has a balance' in reply.view['text']
    assert str(second.public_id) not in reply.view['text']


def test_several_invoices_are_chosen_from_a_list(house):
    second = Invoice.objects.get(pk=house['invoice'].pk)
    second.pk = None
    second.public_id = uuid4()
    second.reference = 'INV-SECOND'
    second.period_start = second.period_start - timedelta(days=31)
    second.save()
    menu = session(house)
    choosing = tap(menu, 'I have already paid')
    assert 'Which invoice did you pay?' in choosing.view['text']
    amount = tap(choosing, 'INV-SECOND')
    assert amount.view['text'].startswith('INV-SECOND')


def test_manager_template_button_opens_the_proof_hours_later(house):
    proof, buttons = manager_buttons(house)
    reply = press(buttons[0])
    assert proof.number in reply.view['text'] and 'Confirm only after' in reply.view['text']
    assert [row['title'] for row in reply.view['options']] == [
        'Confirm received', 'Not received', 'Ask for details', 'Back',
    ]

    done = tap(reply, 'Confirm received')

    proof.refresh_from_db()
    assert proof.status == 'confirmed' and proof.reviewed_by == house['manager']
    assert Payment.objects.filter(proof=proof).count() == 1
    assert proof.payment.receipt_number in done.view['text']
    assert AuditEvent.objects.filter(action='payment_proof.confirmed').exists()


def test_review_button_alone_changes_nothing(house):
    proof, buttons = manager_buttons(house)
    press(buttons[0])
    proof.refresh_from_db()
    assert proof.status == 'submitted' and not Payment.objects.exists()


def test_not_received_needs_a_reason(house):
    proof, buttons = manager_buttons(house)
    asked = press(buttons[1])
    assert 'Why was it not received?' in asked.view['text']
    step('No money in the account')
    proof.refresh_from_db()
    assert (proof.status, proof.review_note) == ('rejected', 'No money in the account')
    assert not Payment.objects.exists()


def test_cancel_during_a_reason_leaves_the_proof_waiting(house):
    proof, buttons = manager_buttons(house)
    press(buttons[1])
    step('cancel')
    proof.refresh_from_db()
    assert proof.status == 'submitted'


def test_ask_then_tenant_answers_with_a_new_revision(house):
    proof, buttons = manager_buttons(house)
    press(buttons[2])
    step('Which account did you pay into?')
    proof.refresh_from_db()
    assert proof.status == 'needs_information'

    from .whatsapp.access import revoke

    revoke(user=house['manager'])
    menu = session(house)
    question = tap(menu, 'I have already paid')
    assert 'Which account did you pay into?' in question.view['text']
    methods = tap(tap(question, 'Answer question'), 'Full balance')
    tap(tap(methods, 'Bank transfer'), 'Today')
    step('NEWREF')
    send_file()
    fetch()
    review = tap(WhatsAppReply.objects.latest('pk'), 'Done')
    tap(review, 'Confirm')

    proof.refresh_from_db()
    assert (proof.status, proof.revision, proof.reference) == ('submitted', 2, 'NEWREF')


def test_old_button_reports_the_current_result(house):
    proof, buttons = manager_buttons(house)
    proofs.confirm(proof, user=house['manager'])
    reply = press(buttons[0])
    assert f'{proof.number} is now: confirmed' in reply.view['text']
    assert Payment.objects.count() == 1


def test_old_button_does_not_apply_to_a_new_revision(house):
    proof, buttons = manager_buttons(house)
    proofs.decline(proof, user=house['manager'], note='Which?', ask=True)
    proofs.resubmit(proof, user=house['tenant'], amount=Decimal('50'), method='mobile_money',
                    paid_on=timezone.localdate(), reference='MP2')
    reply = press(buttons[0])
    assert 'is now' in reply.view['text']
    assert not reply.view['options'] or 'Confirm received' not in str(reply.view['options'])


def test_expired_button_points_to_the_menu_and_keeps_the_proof_waiting(house):
    proof, buttons = manager_buttons(house)
    WhatsAppProofNotice.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
    reply = press(buttons[0])
    assert 'That button has expired' in reply.view['text']
    proof.refresh_from_db()
    assert proof.status == 'submitted'


@pytest.mark.parametrize('payload', ['dw.review.forged', 'dw.delete.forged', 'dw.', 'dw.review.'])
def test_forged_buttons_do_nothing(house, payload):
    report_proof, _ = manager_buttons(house)
    reply = press(payload)
    assert 'no longer available' in reply.view['text'] and not reply.view['options']
    report_proof.refresh_from_db()
    assert report_proof.status == 'submitted'


def test_button_cannot_be_used_from_another_connection(house):
    proof, buttons = manager_buttons(house)
    from .whatsapp.access import revoke

    revoke(user=house['manager'])
    linked(house, 'tenant')
    reply = press(buttons[0])
    assert 'no longer available' in reply.view['text']
    proof.refresh_from_db()
    assert proof.status == 'submitted'


def test_manager_menu_lists_waiting_payments(house):
    proof = report(house)
    menu = session(house, 'manager')
    listing = tap(menu, 'Review payment proof')
    assert proof.number in listing.view['text']
    opened = tap(listing, proof.number)
    assert 'Confirm only after' in opened.view['text']


def test_review_sends_files_then_buttons(house):
    from django.core.files.uploadedfile import SimpleUploadedFile

    linked(house, 'manager')
    PhoneMessagingConsent.objects.update(allowed=True, last_inbound_at=timezone.now())
    proof = report(house, uploads=[SimpleUploadedFile('p.png', png())])
    menu = step()
    if menu.view['text'] == 'Choose your workspace.':
        menu = step(token=menu.view['options'][0]['id'])
    tap(tap(menu, 'Review payment proof'), proof.number)
    with patch('apps.notifications.whatsapp.evidence.post_request', return_value={'id': 'm1'}), \
            patch('apps.notifications.whatsapp.evidence.post_json') as evidence, \
            patch('apps.notifications.whatsapp.transport.post_json',
                  return_value={'messages': [{'id': 'wamid.main'}]}) as main:
        dispatch_replies()
    assert evidence.call_args.args[1]['type'] == 'image'
    assert 'Confirm only after' in main.call_args.args[1]['interactive']['body']['text']


def test_failed_file_send_still_delivers_the_review_with_a_warning(house):
    from django.core.files.uploadedfile import SimpleUploadedFile

    linked(house, 'manager')
    PhoneMessagingConsent.objects.update(allowed=True, last_inbound_at=timezone.now())
    proof = report(house, uploads=[SimpleUploadedFile('p.png', png())])
    menu = step()
    if menu.view['text'] == 'Choose your workspace.':
        menu = step(token=menu.view['options'][0]['id'])
    tap(tap(menu, 'Review payment proof'), proof.number)
    with patch('apps.notifications.whatsapp.evidence.post_request', side_effect=TimeoutError), \
            patch('apps.notifications.whatsapp.transport.post_json',
                  return_value={'messages': [{'id': 'wamid.main'}]}) as main:
        dispatch_replies()
    assert 'could not be sent here' in main.call_args.args[1]['interactive']['body']['text']


def test_duplicate_screenshot_is_flagged_to_the_manager(house):
    from django.core.files.uploadedfile import SimpleUploadedFile

    raw = png()
    first = report(house, uploads=[SimpleUploadedFile('a.png', raw)])
    second = report(house, uploads=[SimpleUploadedFile('b.png', raw)])
    menu = session(house, 'manager')
    opened = tap(tap(menu, 'Review payment proof'), second.number)
    assert f'also on: {first.number}' in opened.view['text']
