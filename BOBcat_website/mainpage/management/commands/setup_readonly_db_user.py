import os
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

_SAFE_IDENTIFIER = re.compile(r'^[a-z][a-z0-9_]{0,62}$')

TABLES = [
    "mainpage_binarymodel",
    "mainpage_papers",
    "mainpage_evidence",
]


class Command(BaseCommand):
    help = (
        "Create (or update) the read-only PostgreSQL role used to execute "
        "user-submitted SQL queries. Reads credentials from the "
        "READONLY_DB_USER and READONLY_DB_PASSWORD environment variables."
    )

    def handle(self, *args, **options):
        user = os.environ.get("READONLY_DB_USER", "bobcat_readonly")
        password = os.environ.get("READONLY_DB_PASSWORD", "")

        if not _SAFE_IDENTIFIER.match(user):
            raise CommandError(
                f"READONLY_DB_USER '{user}' contains invalid characters. "
                "Use lowercase letters, digits, and underscores only."
            )
        if not password:
            raise CommandError(
                "READONLY_DB_PASSWORD is not set. "
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

            cur.execute("SELECT current_database()")
            db_name = cur.fetchone()[0]

            cur.execute(f'GRANT CONNECT ON DATABASE "{db_name}" TO "{user}"')
            cur.execute(f'GRANT USAGE ON SCHEMA public TO "{user}"')

            for table in TABLES:
                cur.execute(f'GRANT SELECT ON "{table}" TO "{user}"')
                self.stdout.write(f"  GRANT SELECT ON {table}")

        self.stdout.write(self.style.SUCCESS(
            f"\nRead-only role '{user}' is ready. "
            f"Add READONLY_DB_USER and READONLY_DB_PASSWORD to your env file "
            f"and restart the container."
        ))
