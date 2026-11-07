import json

from django.core.management.base import BaseCommand, CommandError

from apps.common.release_readiness import snapshot


class Command(BaseCommand):
    help = "Read-only DB, administrator, backup and optional WhatsApp release checks."

    def add_arguments(self, parser):
        parser.add_argument("--require-whatsapp", action="store_true")

    def handle(self, *args, **options):
        result = snapshot(require_whatsapp=options["require_whatsapp"])
        self.stdout.write(json.dumps(result, sort_keys=True))
        if not result["ready"]:
            raise CommandError("Release readiness checks failed. No settings were changed.")
