import os

from django.core.management.base import BaseCommand, CommandError

from apps.common.runtime_database import provision


class Command(BaseCommand):
    help = "Provision a distinct application DB role using maintenance credentials; no URL output."

    def handle(self, *args, **options):
        try:
            result = provision(os.environ.get("APP_RUNTIME_DATABASE_URL", ""))
        except Exception:
            # psycopg exception details can contain the password-bearing SQL.
            raise CommandError(
                "Runtime role provisioning failed; verify maintenance settings."
            ) from None
        self.stdout.write(
            f"Runtime role provisioned for {result['private_tables']} private tables."
        )
