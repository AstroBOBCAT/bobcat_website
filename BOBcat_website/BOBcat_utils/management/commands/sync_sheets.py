from django.core.management.base import BaseCommand
# Import your sync function from the previous step
from BOBcat_utils import ingestion

class Command(BaseCommand):
    help = 'Pulls data from a public Google Sheet and updates the PSQL database'

    def handle(self, *args, **options):
        self.stdout.write('Starting Google Sheet sync...')
        try:
            ingestion.sync_sheet_to_postgres()
            self.stdout.write(self.style.SUCCESS('Successfully synced data!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Sync failed: {e}'))