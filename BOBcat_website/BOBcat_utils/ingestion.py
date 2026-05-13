# utils.py
import pandas as pd
from django.db import transaction
from sourcepage.models import Papers,BinaryModel,Evidence # Assuming Employee is imported from your models

#TODO Add timestamps!

def sync_sheet_to_postgres(sheet_id: str = "DEFAULT"):

    # Get first tab of sheet as CSV
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

    # Pandas reads directly from the URL
    df = pd.read_csv(csv_url)

    # CRITICAL: Pandas parses empty CSV cells as NaN (float).
    # We replace them with empty strings so Django CharFields don't crash.
    df.fillna('', inplace=True)

    # Convert the dataframe to a list of dictionaries for easy iteration
    records = df.values.tolist()

    objects_to_create = [
        Papers(
            paper_link=row[0],
            candidate_name=row[1],
            ned_name=row[2],
            model_param_link=row[3],
            notes = row[5],
        )
        for row in records
    ]

    # Save to PostgreSQL using bulk operations
    with transaction.atomic():
        # Django 4.1+ supports native PostgreSQL UPSERT (Insert or Update)
        Papers.objects.bulk_create(
            objects_to_create,
            update_conflicts=True,
            unique_fields=['paper_link'],  # The unique identifier
            update_fields=['candidate_name','ned_name','notes'],  # Fields to update if email exists
            batch_size=1000  # Insert in chunks of 1000
        )

def sync_binary_models():
    # Loop through all papers
    for paper in Papers.objects.all():
        # update_or_create looks for a record matching the kwargs (e.g., paper=paper)
        # If found, it updates it with the values in 'defaults'
        # If not found, it creates a new record using both kwargs and 'defaults'

        # Get first tab of sheet as CSV
        csv_url = paper.paper_link
        # Pandas reads directly from the URL
        df = pd.read_csv(csv_url)
        df = df.head(30) #get first 30 rows?

        # CRITICAL: Pandas parses empty CSV cells as NaN (float).
        # We replace them with empty strings so Django CharFields don't crash.
        df.fillna('', inplace=True)

        # Convert the dataframe to a list of dictionaries for easy iteration
        records = df.values.tolist()

        objects_to_create = [
            Papers(
                paper_link=row[0],
                candidate_name=row[1],
                ned_name=row[2],
                model_param_link=row[3],
                notes=row[5],
            )
            for row in records
        ]

        # Save to PostgreSQL using bulk operations
        with transaction.atomic():
            # Django 4.1+ supports native PostgreSQL UPSERT (Insert or Update)
            Papers.objects.bulk_create(
                objects_to_create,
                update_conflicts=True,
                unique_fields=['paper_link'],  # The unique identifier
                update_fields=['candidate_name', 'ned_name', 'notes'],  # Fields to update if email exists
                batch_size=1000  # Insert in chunks of 1000
            )
