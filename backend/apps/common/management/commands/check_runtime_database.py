from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Fail if a runtime database login has maintenance privileges or owns application tables."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("A restricted PostgreSQL runtime connection is required.")
        with connection.cursor() as cursor:
            cursor.execute("""SELECT r.rolsuper OR r.rolcreaterole OR r.rolcreatedb
                OR r.rolreplication OR r.rolbypassrls
                OR EXISTS(SELECT 1 FROM pg_auth_members m WHERE m.member=r.oid)
                OR EXISTS(SELECT 1 FROM pg_database d WHERE d.datdba=r.oid)
                OR EXISTS(SELECT 1 FROM pg_class c WHERE c.relowner=r.oid)
                OR EXISTS(SELECT 1 FROM pg_namespace n WHERE n.nspowner=r.oid)
                OR has_schema_privilege(current_user, 'public', 'CREATE')
                FROM pg_roles r WHERE r.rolname=current_user""")
            if cursor.fetchone()[0]:
                raise CommandError("Runtime database login retains maintenance privileges.")
        self.stdout.write("Runtime database login has no maintenance privileges.")
