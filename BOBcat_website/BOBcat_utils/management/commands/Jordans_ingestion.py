from django.core.management.base import BaseCommand
from BOBcat_utils import ingest
import traceback


class Command(BaseCommand):
    help = "Ingest binary model data from a Google Sheet into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sheet-key",
            type=str,
            default=ingest.DEFAULT_SHEET_KEY,
            help="Google Sheets key for the master model list",
        )

    def handle(self, *args, **options):
        sheet_key = options["sheet_key"]
        self.stdout.write(f"Starting ingestion from sheet {sheet_key}...")
        try:
            stats = ingest.ingest(sheet_key)
            self.stdout.write(self.style.SUCCESS(
                f"Ingestion complete: {stats['models']} models created, "
                f"{stats['skipped']} skipped"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ingestion failed: {e}"))
            traceback.print_exc()
