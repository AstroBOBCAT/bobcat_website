from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = (
        "Install the pg_sphere PostgreSQL extension to enable ADQL geometry "
        "functions (CIRCLE, CONTAINS, DISTANCE, …).  Requires a superuser "
        "connection (the default POSTGRES_USER).  Safe to run more than once."
    )

    def handle(self, *args, **options):
        with connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_sphere;")
        self.stdout.write(self.style.SUCCESS(
            "pg_sphere extension is installed.  "
            "ADQL geometry queries are now available."
        ))
