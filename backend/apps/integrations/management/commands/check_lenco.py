import os

from django.core.management.base import BaseCommand, CommandError

from apps.integrations.lenco import LencoClient, LencoError


class Command(BaseCommand):
    help = "Check Lenco token access with one read-only GET; never initiates payments."

    def add_arguments(self, parser):
        parser.add_argument("--environment", choices=("sandbox", "live"), required=True)

    def handle(self, *args, **options):
        environment = options["environment"]
        if os.environ.get("LENCO_ENVIRONMENT") != environment:
            raise CommandError("The selected environment must match LENCO_ENVIRONMENT.")
        try:
            secret = os.environ.get(f"LENCO_{environment.upper()}_SECRET_KEY", "")
            count = LencoClient(secret, environment=environment).check_accounts()
        except LencoError as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(
            self.style.SUCCESS(
                f"Lenco {environment} authentication succeeded. "
                f"Account records on first page: {count}. "
                "No payment was initiated."
            )
        )
