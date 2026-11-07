"""Provision a separate DML-only application login using a maintenance connection."""

import re
from urllib.parse import unquote, urlsplit

from django.conf import settings
from django.db import connection, transaction
from psycopg import sql


def provision(url):
    if settings.DEBUG or connection.vendor != "postgresql":
        raise ValueError("A PostgreSQL maintenance connection is required.")
    desired = urlsplit(url)
    role, password = unquote(desired.username or ""), unquote(desired.password or "")
    config = connection.settings_dict
    if (
        desired.scheme not in {"postgres", "postgresql"}
        or not re.fullmatch(r"dwella_runtime(?:_[a-z0-9_]{1,24})?", role)
        or len(password) < 32
        or desired.hostname != config["HOST"]
        or (desired.port or 5432) != int(config["PORT"] or 5432)
        or unquote(desired.path.lstrip("/")) != config["NAME"]
        or role == config["USER"]
    ):
        raise ValueError(
            "Use a distinct runtime login for this same database and a strong password."
        )
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        if not cursor.fetchone()[0]:
            raise ValueError("Run provisioning through the maintenance connection.")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role])
        if not cursor.fetchone():
            cursor.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
        # Refuse to repurpose an owner or an inherited administrative role.
        cursor.execute(
            """SELECT EXISTS(SELECT 1 FROM pg_auth_members m
            JOIN pg_roles r ON r.oid=m.member WHERE r.rolname=%s)
            OR EXISTS(SELECT 1 FROM pg_database d JOIN pg_roles r ON r.oid=d.datdba
            WHERE r.rolname=%s)
            OR EXISTS(SELECT 1 FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner
            WHERE r.rolname=%s)
            OR EXISTS(SELECT 1 FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner
            WHERE r.rolname=%s)""",
            [role] * 4,
        )
        if cursor.fetchone()[0]:
            raise ValueError("Runtime role must have no ownership or inherited privileges.")
        cursor.execute(
            sql.SQL(
                "ALTER ROLE {} WITH LOGIN NOSUPERUSER NOCREATEDB "
                "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS PASSWORD {}"
            ).format(sql.Identifier(role), sql.Literal(password))
        )
        cursor.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(config["NAME"]), sql.Identifier(role)
            )
        )
        cursor.execute(sql.SQL("REVOKE ALL ON SCHEMA public FROM {}").format(sql.Identifier(role)))
        cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
        cursor.execute("SELECT has_schema_privilege(%s, 'public', 'CREATE')", [role])
        if cursor.fetchone()[0]:
            raise ValueError("Remove public schema CREATE privileges before provisioning runtime.")
        cursor.execute(
            sql.SQL(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES " "IN SCHEMA public TO {}"
            ).format(sql.Identifier(role))
        )
        cursor.execute(
            sql.SQL(
                "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES " "IN SCHEMA public TO {}"
            ).format(sql.Identifier(role))
        )
        cursor.execute(
            sql.SQL("REVOKE INSERT, UPDATE, DELETE ON django_migrations FROM {}").format(
                sql.Identifier(role)
            )
        )
        # Future migrations run as the same maintenance owner. Private RLS tables
        # still need the explicit runtime policy below after each migration batch.
        cursor.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT "
                "SELECT, INSERT, UPDATE, DELETE ON TABLES TO {}"
            ).format(sql.Identifier(role))
        )
        cursor.execute(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT "
                "USAGE, SELECT, UPDATE ON SEQUENCES TO {}"
            ).format(sql.Identifier(role))
        )
        cursor.execute(
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity"
        )
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(
                sql.SQL("DROP POLICY IF EXISTS dwella_runtime_access ON {}").format(
                    sql.Identifier(table)
                )
            )
            cursor.execute(
                sql.SQL(
                    "CREATE POLICY dwella_runtime_access ON {} TO {} "
                    "USING (true) WITH CHECK (true)"
                ).format(sql.Identifier(table), sql.Identifier(role))
            )
    return {"private_tables": len(tables), "runtime_role": role}
