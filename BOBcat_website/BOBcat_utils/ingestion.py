# utils.py
import io
import re

import pandas as pd
import requests
import io
from django.db import transaction
from sourcepage.models import Papers,BinaryModel,Evidence # Assuming Employee is imported from your models

#TODO Add timestamps!

def sync_sheet_to_postgres(sheet_id: str = "1SPegAdb2lL7o0oiMk7qSjwz9oCgkFJ3RCR7RMcworaw", gid : str ="0"):
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    try:
        # 1. Fetch the data using requests to check the status
        response = requests.get(csv_url, timeout=10)
        response.raise_for_status()  # Raises an error if the page is 404 or requires login (401/403)

        # 2. Read into pandas safely
        df = pd.read_csv(io.StringIO(response.text))
        print("Successfully loaded dataframe!")

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}. Is the sheet public?")
    except Exception as e:
        print(f"An error occurred: {e}")

    print(df.head()) #debug
    # CRITICAL: Pandas parses empty CSV cells as NaN (float).
    # We replace them with empty strings so Django CharFields don't crash.
    df.fillna('', inplace=True)
    # Returns True if any value in 'column_name' is a duplicate
    if df[df.columns[3]].duplicated().any():
        raise ValueError(f'Duplicate model links in ingested PAPER csv {csv_url}.\n'
                         f'Model Parameter Links MUST be unique!')

    # Convert the dataframe to a list of dictionaries for easy iteration
    records = df.values.tolist()

    objects_to_create = [
        Papers(
            paper_link=row[0],
            candidate_name=row[1],
            ned_name=row[2],
            model_param_link=row[3],
            notes = row[4],
        )
        for row in records
    ]

    # Save to PostgreSQL using bulk operations
    with transaction.atomic():
        # Django 4.1+ supports native PostgreSQL UPSERT (Insert or Update)
        Papers.objects.bulk_create(
            objects_to_create,
            batch_size=1000,
            update_conflicts=True,
            unique_fields=['paper_link'],  # The unique field that determines if it's a duplicate
            update_fields=[  # The fields to update if a duplicate is found
                'candidate_name',
                'ned_name',
                'model_param_link',
                'notes'
            ]
        )


def get_google_sheet_data(url):
    # 1. Extract the sheet_id using a regular expression
    # Looks for "/d/" followed by any characters that aren't a slash
    sheet_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)

    if not sheet_id_match:
        raise ValueError("Could not find a valid sheet_id in the provided URL."+url)

    sheet_id = sheet_id_match.group(1)

    # 2. Extract the gid (tab ID) if it exists, otherwise default to "0" (first tab)
    gid_match = re.search(r'[#&?]gid=([0-9]+)', url)
    gid = gid_match.group(1) if gid_match else "0"

    print(f"Extracted Sheet ID: {sheet_id}")
    print(f"Extracted GID: {gid}")

    # 3. Construct the proper export URL
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    # 4. Fetch and read the data
    try:
        response = requests.get(export_url, timeout=10)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text))
        print("Successfully loaded dataframe!")
        return df,sheet_id

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}. Ensure the sheet is set to 'Anyone with the link can view'.")
    except Exception as e:
        print(f"An error occurred: {e}")
def sync_binary_models():
    # Loop through all papers
    objects_to_create = []
    csv_links = []
    for paper in Papers.objects.all():

        # Get first tab of sheet as CSV
        csv_url = paper.model_param_link
        if csv_url in csv_links:
            print("There is a duplicate link in your Papers Table!\n"
                  "This should not be happening, please go check on it!")
            continue
        else:
            csv_links.append(csv_url)

        # Pandas reads directly from the URL
        df,name = get_google_sheet_data(csv_url)
        df = df.head(30) #get first 30 rows?

        #None works here because django can handle blank entries.
        df.fillna(None, inplace=True)

        # Convert the dataframe to a list of dictionaries for easy iteration
        records = df.set_index("Name")["Value"].to_dict()
        objects_to_create.append(
            BinaryModel(
                model_param_link=csv_url,
                sheet_id= name,
                paper=records.get("paper link",None),
                candidate_name=records.get("source_name",None),
                eccentricity=records.get("eccentricity",None),
                m1 = records.get("m1",None),
                m2 = records.get("m2",None),
                mtot = records.get("total mass",None),
                mc = records.get("chirp mass",None),
                mu = records.get("reduced mass",None),
                q = records.get("q",None),
                inclination= records.get("inclination",None),
                semimajor_axis= records.get("semi=major axis",None),
                seperation= records.get("separation",None),
                period_epoch= records.get("period epoch",None),
                orb_freq= records.get("orbital frequency (earth frame)",None),
                orb_period= records.get("orbital period (earth frame)",None),
                summary= records.get("Summary/notes on source", None),
                caveats= records.get("Caveats",None),
            )
        )
        #loop end

    # Save to PostgreSQL using bulk operations
    with transaction.atomic():
        # Django 4.1+ supports native PostgreSQL UPSERT (Insert or Update)
        BinaryModel.objects.bulk_create(
            objects_to_create,
            batch_size=1000,
            update_conflicts=True,
            unique_fields=['model_param_link'],  # Now your primary key!
            update_fields=[
                'paper',
                'eccentricity',
                'm1',
                'm2',
                'mtot',
                'mc',
                'mu',
                'q',
                'inclination',
                'semimajor_axis',
                'seperation',
                'period_epoch',
                'orb_freq',
                'orb_period',
                'summary',
                'caveats',
                'ext_proj',
                'gw_strain',
                'gw_freq',
                'gw_strain_err',
                'gw_freq_err'
                # Do NOT include model_param_link in update_fields
            ]
        )

