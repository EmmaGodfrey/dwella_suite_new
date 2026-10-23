from django.core.management.base import BaseCommand
from django.db import transaction

from apps.outreach.models import OutreachSettings, Sequence, SequenceStep, Template


class Command(BaseCommand):
    help = (
        "Create editable outreach starter sequences without overwriting edits or adding contacts."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        OutreachSettings.objects.get_or_create(pk=1)
        starters = [
            (
                "Influencer partnership",
                "influencer",
                [
                    (
                        0,
                        "Dwella × {handle}: partnership idea",
                        "Hi {first_name},\n\n{personal_line}\n\n"
                        "I'm {sender_first_name} from EG Labs in Lusaka. We're building Dwella, a "
                        "property "
                        "management app for Zambian landlords and agents: rent tracking, receipts, "
                        "arrears "
                        "and maintenance in one place. Our beta opens on 18 November.\n\n"
                        "I'd love to explore a partnership. We can offer {offer}. Would you "
                        "be open "
                        "to "
                        "a 15-minute call this week or next?\n\n{signature}",
                    ),
                    (
                        4,
                        "Re: Dwella × {handle}: partnership idea",
                        "Hi {first_name}, just bringing this back to the top of your inbox. Happy "
                        "to send "
                        "a short demo video first if that's easier.\n\n{signature_short}",
                    ),
                    (
                        6,
                        "Re: Dwella × {handle}: partnership idea",
                        "Hi {first_name}, I'll leave it here so I don't crowd your inbox. If a "
                        "partnership "
                        "around the 18 December launch is interesting later, just "
                        "reply.\n\n{signature_short}",
                    ),
                ],
            ),
            (
                "Agent beta invite",
                "agent",
                [
                    (
                        0,
                        "Free beta access to Dwella for {organization}",
                        "Dear {salutation},\n\n{personal_line}\n\nI'm {sender_first_name} from EG "
                        "Labs. "
                        "We're building Dwella for rentals in Zambia: tenants, leases, rent and "
                        "receipts, "
                        "arrears and repairs in one place, on your phone or computer.\n\nWe're "
                        "opening a "
                        "free beta on 18 November for a small group of agents and property "
                        "managers. "
                        "Reserve a place at dwella.properties, or reply and I'll help set up your "
                        "account."
                        "\n\n{signature}",
                    ),
                    (
                        5,
                        "Re: Free beta access to Dwella for {organization}",
                        "Dear {salutation}, a quick follow-up on the Dwella beta. Would a short "
                        "demo help?"
                        "\n\n{signature_short}",
                    ),
                    (
                        7,
                        "Re: Free beta access to Dwella for {organization}",
                        "Dear {salutation}, I'll leave it here. If you'd like to try Dwella later, "
                        "just reply and we'll get you started.\n\n{signature_short}",
                    ),
                ],
            ),
            (
                "Early tester check-ins",
                "other",
                [
                    (
                        3,
                        "How's Dwella going so far?",
                        "Hi {first_name}, how has your first few days with Dwella been? If "
                        "anything "
                        ""
                        "is confusing or gets in your way, reply and I'll "
                        "help.\n\n{signature_short}",
                    ),
                    (
                        7,
                        "Three quick questions about Dwella",
                        "Hi {first_name}, could you share what you tried in Dwella, what got "
                        "in the "
                        "way, "
                        "and whether you would recommend it? Your feedback shapes what we build."
                        "\n\n{signature_short}",
                    ),
                ],
            ),
        ]
        for name, segment, steps in starters:
            sequence, created = Sequence.objects.get_or_create(name=name)
            if not created:
                continue
            for order, (wait_days, subject, body) in enumerate(steps):
                template, _ = Template.objects.get_or_create(
                    name=f"{name} / Step {order + 1}",
                    defaults={
                        "segment": segment,
                        "subject": subject,
                        "body": body,
                        "whatsapp_body": body,
                        "is_follow_up": order > 0,
                    },
                )
                SequenceStep.objects.create(
                    sequence=sequence, template=template, order=order, wait_days=wait_days
                )
        self.stdout.write("Editable starter sequences ready. No contacts added or emails sent.")
