import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

_SAFE_IDENTIFIER = re.compile(r'^[a-z][a-z0-9_]{0,62}$')


class Command(BaseCommand):
    help = (
        "Create (or update) the non-superuser PostgreSQL role the web "
        "application uses at runtime. It gets DML (SELECT/INSERT/UPDATE/DELETE) "
        "on the public schema but no DDL, no superuser, and no role/database "
        "creation, so a compromised gunicorn process can't alter the schema, "
        "read server files, or touch other databases. Migrations and "
        "CREATE EXTENSION still run as the superuser POSTGRES_USER from the "
        "entrypoint; only the serving process drops to this role. Reads "
        "credentials from APP_DB_USER and APP_DB_PASSWORD."
    )

    def handle(self, *args, **options):
        user = os.environ.get("APP_DB_USER", "bobcat_app")
        password = os.environ.get("APP_DB_PASSWORD", "")

        if not _SAFE_IDENTIFIER.match(user):
            raise CommandError(
                f"APP_DB_USER '{user}' contains invalid characters. "
                "Use lowercase letters, digits, and underscores only."
            )
        if not password:
            raise CommandError(
                "APP_DB_PASSWORD is not set. "
                "Add it to your .db_info env file and retry."
            )

        with connection.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = %s", [user]
            )
            if cur.fetchone():
                cur.execute(f'ALTER ROLE "{user}" WITH LOGIN PASSWORD %s', [password])
                self.stdout.write(f"Updated password for existing role '{user}'.")
            else:
                cur.execute(f'CREATE ROLE "{user}" WITH LOGIN PASSWORD %s', [password])
                self.stdout.write(f"Created role '{user}'.")

            # Explicitly deny the traits that make a superuser dangerous, in
            # case the role pre-existed with them.
            cur.execute(
                f'ALTER ROLE "{user}" WITH NOSUPERUSER NOCREATEDB NOCREATEROLE'
            )

            cur.execute("SELECT current_database()")
            db_name = cur.fetchone()[0]

            cur.execute(f'GRANT CONNECT ON DATABASE "{db_name}" TO "{user}"')
            cur.execute(f'GRANT USAGE ON SCHEMA public TO "{user}"')

            # DML on existing tables/sequences, and the same as a default for
            # anything future migrations create, so this command doesn't have
            # to be re-run table-by-table after every schema change (the
            # entrypoint re-runs it after `migrate` regardless).
            cur.execute(
                f'GRANT SELECT, INSERT, UPDATE, DELETE '
                f'ON ALL TABLES IN SCHEMA public TO "{user}"'
            )
            cur.execute(
                f'GRANT USAGE, SELECT, UPDATE '
                f'ON ALL SEQUENCES IN SCHEMA public TO "{user}"'
            )
            cur.execute(
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public '
                f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{user}"'
            )
            cur.execute(
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public '
                f'GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO "{user}"'
            )

            # No DDL and no reach into Postgres internals.
            cur.execute(f'REVOKE CREATE ON SCHEMA public FROM "{user}"')
            cur.execute(f'REVOKE ALL ON SCHEMA pg_catalog FROM "{user}"')
            cur.execute(f'REVOKE ALL ON SCHEMA information_schema FROM "{user}"')

        self.stdout.write(self.style.SUCCESS(
            f"\nApplication role '{user}' is ready (non-superuser, DML only)."
        ))
