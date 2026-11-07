"""Menu-first intake does not infer a financial action from unsolicited input."""
import pytest

from apps.billing.models import PaymentProof

from . import test_whatsapp as base
from .test_whatsapp import choose, step, workspace
from .test_whatsapp_proof_flow import send_file
from .whatsapp.models import WhatsAppConversation, WhatsAppMedia

pytestmark = pytest.mark.django_db
config = base.config
house = base.house


def test_unknown_text_returns_menu_without_starting_a_draft(house):
    workspace(house)
    reply = step('Please make some changes for me')
    assert 'Please choose an option below.' in reply.view['text']
    assert reply.view['options'] and not WhatsAppConversation.objects.get().draft


def test_unrequested_file_does_not_start_a_payment_or_fetch_media(house):
    workspace(house)
    reply = send_file()
    assert 'Choose I have already paid or Report a repair first.' in reply.view['text']
    assert not WhatsAppMedia.objects.exists() and not PaymentProof.objects.exists()


def test_create_invoice_is_explicit_website_handoff(house):
    menu = workspace(house, 'manager')
    reply = step(token=choose(menu, 'Create invoice in Dwella'))
    assert 'Create and review invoices in Dwella:' in reply.view['text']
    assert '/billing' in reply.view['text'] and 'not on WhatsApp yet' not in reply.view['text']


def test_file_before_requested_payment_evidence_step_is_not_downloaded(house):
    menu = workspace(house)
    step(token=choose(menu, 'I have already paid'))
    send_file()
    assert not WhatsAppMedia.objects.exists()
    assert WhatsAppConversation.objects.get().draft['step'] == 'amount'


@pytest.mark.parametrize('command', ['MENU', 'CANCEL', 'BACK'])
def test_control_commands_exit_unsubmitted_draft(house, command):
    menu = workspace(house)
    step(token=choose(menu, 'I have already paid'))
    reply = step(command)
    assert not WhatsAppConversation.objects.get().draft
    assert not PaymentProof.objects.exists() and reply.view['options']
