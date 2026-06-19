#########

## This ingestion script is to be used for ingesting sources from a
## google spreadsheet. This was choosen as the offline verison on
## BOBcat that was created and used to collected candidates before
## BOBcat started and while BOBcat was in the beginning stages is in a
## google spreadsheet. However, this ingestion script could be used
## for any google spreadsheet that is setup in the correct way and
## that the key for is known.

## There should be another ingestion script that deals with pulling
## data for other databases so candidates from large surveys, such as
## CRTs, are easy to ingest into BOBcat without having to create an
## entry into a google spreadsheet for every single candidate in the
## surveys.

#########

from math import nan
from types import NoneType
import pandas as pd #pandas dataframe that the csv file information gets read into for easy manipulation in python
import numpy as np #numpy
import psycopg
import psycopg2
from logging import warning
from logging import info
import time
from astropy.coordinates import SkyCoord
from astropy.time import Time
import os

from astroquery.ipac.ned import Ned
Ned.clear_cache()
# Import the utilities made for BOBcat itself and the specific ingestion utilities made for this process.

#seems to be querying some astro databases like redshift and ned.
from BOBcat_utils import astrodb as astrodb
#helper for astro utilities
from BOBcat_utils import calc


## This is used to create the full url needed for having the information in the expected google 
## spreadsheet that is outputted into a csv file. All the function needs is the google spreadsheet key that can
## be found in the google spreadsheet link. Note that the link in the browser when you open a google
## spreadsheet will contain the key needed but it is not the correct url needed. Hence this function
## was created to make sure the url was the correct format needed.

##############
# SARAH! This key needs to stay key because it's referenced by both
# the master and parameter extraction functions.
##############

def db_connect():
    conn = psycopg.connect(
        dbname= os.environ.get('POSTGRES_DB', 'bobcat'),
        user= os.environ.get('POSTGRES_USER', 'postgres'),
        password= os.environ.get('POSTGRES_PASSWORD', ''),
        host= os.environ.get('POSTGRES_HOST', 'db'),
        port= os.environ.get('POSTGRES_PORT', '5432'),
    )

    # Create a cursor instance within the database that allows you to enter SQL commands through python.
    cur = conn.cursor()

    return cur, conn

def create_url(key):

    '''.

    Create url for a google spreadsheet such that it is in csv format
    given the spreadsheet key.
    
    Inputs:
        key - this is a long string of random letters and numbers found in all the links to the 
        google spreadsheet in question
        
    Outputs:
        url string

    '''

    # First we need to check that the key given is actually a string.
    # If it isn't a string we could change it into a string but it is
    # probably better to raise an error to make sure the user is aware
    # of what is wanted for the function.
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    # Concatenate the key with the needed strings. The last portion is
    # what turns the google spreadsheet into csv format which makes it
    # very easy to read into a pandas dataframe in other functions.
    url = "https://docs.google.com/spreadsheet/ccc?key=" + key + "&output=csv"
    return url

def ads_to_scix(link):
    """
    Convert ADS links to SciX links. Also returns doi.
    Leaves other links unchanged.
    Inputs:
        link - string of the link to convert
    Outputs:
        new_link - string of the converted link
    """
    if "ui.adsabs" in str(link):
        key = str(link).split("/")[-2]
        new_link = "https://scixplorer.org/abs/" + key
        info(f"Converted ADS link {link} to SciX link {new_link}")
        return new_link, key
    else:
        return str(link), np.nan

#############

def check_binary_model(model, url):
    """
    Check if everything is the right dtype, and if so, check if it fits in the ranges of values that are expected for the binary model parameters.
    Inputs:
        model - pandas dataframe of the model
        url - string of the url to the google spreadsheet
        
    Outputs:
        summary_list_warnings - list of strings of warnings that are raised if the model is not in the expected ranges
        weirdness - A boolean that is True if any part of the model is not in the expected ranges
    """
    
    str_i = ['paper link','source name','Summary/notes on source','Caveats', 'Extension project'] # The indices in the table where we expect strings
    float_i = ['eccentricity','log(m1)','log(m2)','log(total mass)','log(chirp mass)','log(reduced mass)','q','inclination','semi-major axis','separation','period epoch','orbital frequency (earth frame)','orbital period (earth frame)'] # The indices in the table where we expect floats
    summary_list_warnings = []

    # Making sure the string data is in the right format
    for i in str_i:
        if type(model.loc[i].values[0]) != str:
            try:
                model.loc[i].values[0] = str(model.loc[i].values[0])
            except:
                raise TypeError(f"{model.loc[i].values[0]} must be a string. {type(model.loc[i].values[0])} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if len(str(model.loc['Caveats'].values[0])) > 750: # TODO: Determine final max length for notes
        raise ValueError(f"Caveats must be less than 750 characters. {len(model.loc['Caveats'].values[0])} characters given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if len(str(model.loc['Summary/notes on source'].values[0])) > 750: # TODO: Determine final max length for notes
        raise ValueError(f"Summary must be less than 750 characters. {len(model.loc['Summary/notes on source'].values[0])} characters given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
            
    # Check if the values are in the right range and are all floats
    for i in float_i:
        try:
            float(model.loc[i].values[0])
        except:
            raise TypeError(f"{model.loc[i].values[0]} must be a float. {type(model.loc[i].values[0])} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['eccentricity'].values[0]) < 0 or float(model.loc['eccentricity'].values[0]) > 1:
        raise ValueError(f"Eccentricity must be between 0 and 1. {model.loc['eccentricity'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['log(m1)'].values[0]) < 4 or float(model.loc['log(m1)'].values[0]) > 12:
        raise ValueError(f"m1 must be between 4 and 12. {model.loc['log(m1)'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['log(m2)'].values[0]) < 4 or float(model.loc['log(m2)'].values[0]) > 12:
        raise ValueError(f"m2 must be between 4 and 12. {model.loc['log(m2)'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['log(total mass)'].values[0]) < 4 or float(model.loc['log(total mass)'].values[0]) > 12:
        raise ValueError(f"mtot must be between 4 and 12. {model.loc['log(total mass)'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['log(chirp mass)'].values[0]) < 4 or float(model.loc['log(chirp mass)'].values[0]) > 12:
        raise ValueError(f"mc must be between 4 and 12. {model.loc['log(chirp mass)'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['log(reduced mass)'].values[0]) < 4 or float(model.loc['log(reduced mass)'].values[0]) > 12:
        raise ValueError(f"mu must be between 4 and 12. {model.loc['log(reduced mass)'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['q'].values[0]) <= 0 or float(model.loc['q'].values[0]) > 1:
        raise ValueError(f"q must be between 0 and 1. {model.loc['q'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['inclination'].values[0]) < 0 or float(model.loc['inclination'].values[0]) > 90:
        raise ValueError(f"Inclination must be between 0 and 90. {model.loc['inclination'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['semi-major axis'].values[0]) < 0 or float(model.loc['semi-major axis'].values[0]) > 1000:
        raise ValueError(f"Semimajor axis must be between 0 and 1000. {model.loc['semi-major axis'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['separation'].values[0]) < 0 or float(model.loc['separation'].values[0]) > 1000:
        raise ValueError(f"Seperation must be between 0 and 1000. {model.loc['separation'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['period epoch'].values[0]) < 40000 or float(model.loc['period epoch'].values[0]) > Time.now().mjd:
        raise ValueError(f"Period epoch must be between 40000 and current date {Time.now().mjd} MJD. {model.loc['period epoch'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['orbital frequency (earth frame)'].values[0]) < 0:
        raise ValueError(f"Orb freq must be greater than 0. {model.loc['orbital frequency (earth frame)'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    if float(model.loc['orbital period (earth frame)'].values[0]) < 0:
        raise ValueError(f"Orb period must be greater than 0. {model.loc['orbital period (earth frame)'].values[0]} given. NED Name: {model.loc["source name"].values[0]}, url: {url}")
    
    # Check that the values make sense. Won't throw an error for these; could be intentional weirdness.
    # Checks that a value is given for each param, and that an expected value can be calculated, and then checks whether they are within 0.1% of each other.
    weirdness = False # A flag to add this model to odd_params. False by default.
    if not pd.isnull(model.loc["log(total mass)"].values[0]) and not pd.isnull(calc.Mtot_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) and abs(float(model.loc["log(total mass)"].values[0]) - calc.Mtot_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) > 0.001 * calc.Mtot_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0])):
        warning(f"Mtot does not match M1 + M2. \nMtot: {model.loc["log(total mass)"].values[0]} \nM1 + M2: {calc.Mtot_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))} \nNED Name: {model.loc["source name"].values[0]}, url: {url}")
        summary_list_warnings.append(f"\nBinary model for {model.loc["source name"].values[0]} had Mtot != M1 + M2. url: {url}")
        weirdness = True
    if not pd.isnull(model.loc["log(chirp mass)"].values[0]) and not pd.isnull(calc.Mc_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) and abs(float(model.loc["log(chirp mass)"].values[0]) - calc.Mc_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) > 0.001 * calc.Mc_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0])):
        warning(f"Mc value does not match given M1, M2. \nGiven Mc: {model.loc["log(chirp mass)"].values[0]} \nCalculated Mc: {calc.Mc_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))} \nNED Name: {model.loc["source name"].values[0]}, url: {url}")
        summary_list_warnings.append(f"\nBinary model for {model.loc["source name"].values[0]} had Mc inconsistent with M1 and M2. url: {url}")
        weirdness = True
    if not pd.isnull(model.loc["log(reduced mass)"].values[0]) and not pd.isnull(calc.mu_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) and abs(float(model.loc["log(reduced mass)"].values[0]) - calc.mu_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) > 0.001 * calc.mu_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0])):
        warning(f"mu value does not match given M1, M2. \nGiven mu: {model.loc["log(reduced mass)"].values[0]} \nCalculated mu: {calc.Mc_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))} \nNED Name: {model.loc["source name"].values[0]}, url: {url}")
        summary_list_warnings.append(f"\nBinary model for {model.loc["source name"].values[0]} had mu inconsistent with M1 and M2. url: {url}")
        weirdness = True
    if not pd.isnull(model.loc["q"].values[0]) and not pd.isnull(calc.q_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) and abs(float(model.loc["q"].values[0]) - calc.q_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))) > 0.001 * calc.q_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0])):
        warning(f"q value does not match given M1, M2. \nGiven q: {model.loc["q"].values[0]} \nCalculated q: {calc.q_calc(float(model.loc["log(m1)"].values[0]), float(model.loc["log(m2)"].values[0]))} \nNED Name: {model.loc["source name"].values[0]}, url: {url}")
        summary_list_warnings.append(f"\nBinary model for {model.loc["source name"].values[0]} had q inconsistent with M1 and M2. url: {url}")
        weirdness = True
    if model.loc["eccentricity"].values[0] == str(0) and abs(float(model.loc["semi-major axis"].values[0]) - float(model.loc["separation"].values[0])) > 0.001 * float(model.loc["separation"].values[0]):
        warning(f"Orbit doesn't make sense for {model.loc["source name"].values[0]}. e = 0 but a != sep.\nGiven a: {model.loc["semi-major axis"].values[0]}\n Given sep: {model.loc["separation"].values[0]} \nurl: {url}")
        summary_list_warnings.append(f"Conflicting orbital parameters for {model.loc["source name"].values[0]}: circular orbit, but semi-major axis != separation. url: {url}")
        weirdness = True
    if not pd.isnull(float(model.loc["orbital period (earth frame)"].values[0])) and abs(float(model.loc["orbital period (earth frame)"].values[0]) - calc.freq_calc(f_orb = float(model.loc["orbital frequency (earth frame)"].values[0]))[1]) > 0.001 * calc.freq_calc(f_orb = float(model.loc["orbital frequency (earth frame)"].values[0]))[1]:
        warning(f"Orbital period inconsistent with orbital frequency for {model.loc["source name"].values[0]}, url: {url}\nGiven frequency: {model.loc["orbital period (earth frame)"].values[0]}\nCalculated frequency: {calc.freq_calc(f_orb = float(model.loc["orbital frequency (earth frame)"].values[0]))[1]}")
        summary_list_warnings.append(f"Conflicting orbital parameters for {model.loc["source name"].values[0]}: orbital period does not match orbital frequency. url: {url}")
        weirdness = True
    return summary_list_warnings, weirdness

def check_errs(model, model_errs, url):
    '''
    Checks the error values and types for each model.
    Inputs:
        - dictionary containing the error values and types for each model
    Outputs:
        - list of warnings
        - boolean flag for odd params
    '''
    # Every error value should be a string from a pre-defined set
    summary_list_warnings = []
    weirdness = False
    err_types = ["Assumed", "Upper limit", "Lower limit", "Gaussian", "Two sided", "Range", "Representative"]
    if not all([err_type in err_types for err_type in model_errs["Error Type"]]):
        raise ValueError(f"Error types are not valid for url: {url}")

    for prop in model_errs.index:
        if model_errs.loc[prop, "error_lower"] >= model[prop]/2:
            warning(f"Suspiciously high error value for {prop} in {model.loc["source name"].values[0]}:\n Modeled value: {model[prop]}\n Error value: {model_errs.loc[prop, 'error_lower']}\n url: {url}")
            summary_list_warnings.append(f"Suspiciously high error for {prop} in {model.loc["source name"].values[0]}: {model_errs.loc[prop, 'error_lower']}")
            weirdness = True
        elif model_errs.loc[prop, "error_upper"] >= model[prop]/2:
            warning(f"Suspiciously high error value for {prop} in {model.loc["source name"].values[0]}:\n Modeled value: {model[prop]}\n Error value: {model_errs.loc[prop, 'error_upper']}\n url: {url}")
            summary_list_warnings.append(f"Suspiciously high error for {prop} in {model.loc["source name"].values[0]}: {model_errs.loc[prop, 'error_upper']}")
            weirdness = True
    
        if model_errs.loc[prop, "error_upper"] < 0:
            warning(f"Negative upper error value for {prop} in {model.loc["source name"].values[0]}: {model_errs.loc[prop, 'error_upper']}\n url: {url}")
            summary_list_warnings.append(f"Negative upper error for {prop} in {model.loc["source name"].values[0]}: {model_errs.loc[prop, 'error_upper']}")
            weirdness = True
        if model_errs.loc[prop, "error_lower"] > 0:
            warning(f"Positive lower error value for {prop} in {model.loc["source name"].values[0]}: {model_errs.loc[prop, 'error_lower']}\n url: {url}")
            summary_list_warnings.append(f"Positive lower error for {prop} in {model.loc["source name"].values[0]}: {model_errs.loc[prop, 'error_lower']}")
            weirdness = True

    return summary_list_warnings, weirdness

def value_filling(model, summary_list_value_filling, summary_list_warnings, url):
    '''
    Fills in missing values in the model array.
    Inputs:
        - array containing the candidate parameters
        - list to append success messages to
        - list to append warning messages to
        - url of the model, for easy access
    Outputs:
        - value filled model
        - a boolen which is used to make a final cound of value filled models in the summary
    '''
    fills = False
    # Mass values
    masses = pd.Series()
    try:
        masses = calc.mass_val_calc(m1 = float(model.loc['log(m1)'].values[0]), m2 = float(model.loc['log(m2)'].values[0]), Mtot = float(model.loc['log(total mass)'].values[0]), q = float(model.loc['q'].values[0]), Mc = float(model.loc['log(chirp mass)'].values[0]), mu = float(model.loc['log(reduced mass)'].values[0]))
        masses = pd.Series(masses, index=['log(m1)', 'log(m2)', 'log(total mass)', 'log(chirp mass)', 'log(reduced mass)', 'q'])
    except Exception as e:
        #raise e
        warning(f"Unable to calculate mass values for {model.loc["source name"].values[0]}, url: {url}\n exception: {e}")
        summary_list_warnings.append(f"Unable to calculate mass values for {model.loc["source name"].values[0]}, url: {url}")
    # Frequency parameters
    freq_params = pd.Series()
    try:
        freq_params = calc.freq_calc(T = float(model.loc['orbital period (earth frame)'].values[0]), f_orb = float(model.loc['orbital frequency (earth frame)'].values[0]))
        freq_params = pd.Series(freq_params[:2], index=['orbital frequency (earth frame)','orbital period (earth frame)'])
        info(f"Calculated freq params for {model.loc["source name"].values[0]}: {freq_params}")
    except Exception as e:
        freq_params = pd.Series([np.nan, np.nan], index=['orbital period (earth frame)', 'orbital frequency (earth frame)'])
        #raise e
        warning(f"Unable to calculate frequency values for {model.loc['source name'].values[0]}, url: {url}\n exception: {e}")
        summary_list_warnings.append(f"Unable to calculate frequency and period for {model.loc["source name"].values[0]}, url: {url}")
    
    filled_model = model
    if not masses.empty:
        summary_list_value_filling.append(f"Mass values filled for {model.loc["source name"].values[0]}:")
        for i in masses.index:
            if pd.isnull(filled_model.loc[i].values[0]):
                filled_model.loc[i] = str(masses[i]) # Can only store 1 dtype in a df at a time.
                summary_list_value_filling.append(f"Index {i} assigned value {filled_model.loc[i]}") 
                fills = True
                # TODO: Make it so this says explicitly the name of the parameter being filled rather than just the index.
    if not freq_params.empty:
        summary_list_value_filling.append(f"Frequency values filled for {model.loc["source name"].values[0]}:")
        for i in freq_params.index:
            if pd.isnull(float(filled_model.loc[i].values[0])): # frequency nan values must be converted to float because I replace them with np.nans earlier in this method and when ingested into the df they are converted to strings
                filled_model.loc[i] = str(freq_params[i])
                summary_list_value_filling.append(f"Index {i} assigned value {filled_model.loc[i]}")
                fills = True

    return filled_model, fills

################
def ingest_candidate(candidate):

    ''' Ingests a single candidate into a predefined database.

    Inputs:
        array containing the candidate parameters
    Outputs:
        NONE
    '''
    info("in ingest_candidate")

    cur, conn = db_connect()

    info("connected to the database")

    # Ingest the model into the database.
#    cur.execute("INSERT INTO candidate(\
#        name, \
#        ra_deg, \
#        dec_deg,\
#        redshift, \
#        obs_type_done) \
#        VALUES (%s,%s,%s,%s,%s);", candidate)
    cur.execute(
            """
            INSERT INTO candidate (
                jra, jdec, redshift, lum_dist, rating, created_at 
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING candidate_id, lum_dist;
            """,
            candidate[1:]
        )
    conn.commit() #make sure to actually commit the SQL command to the database
    # Always make sure to close the connection to the database 
    # (much like you should always close a file when done with it).
    conn.close()
###############

################
def ingest_binary_model(binary_model, candidate_id, bib_id):

    ''' Ingests a single binary model into a predefined database.

    Inputs:
        array containing the binary model class parameters
    Outputs:
        The newly minted binary model ID.
    '''
    info("in ingest_binary_model")

    cur, conn = db_connect()

    # Ingest the model into the database.
    cur.execute(
    """
    INSERT INTO binary_model (
        candidate_id,
        bibliography_id,
        paper,
        candidate_name,
        eccentricity,
        m1,
        m2,
        mtot,
        mc,
        mu,
        q,
        inclination,
        semimajor_axis,
        seperation,
        period_epoch,
        orb_freq,
        orb_period,
        gw_strain,
        gw_inspiral_timescale,
        summary,
        caveats,
        ext_proj,
        created_at
    ) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING binary_model_id;
    """, [candidate_id, bib_id, *binary_model, created_at])

    binary_model_id = cur.fetchone()[0]
    conn.commit() #make sure to actually commit the SQL command to the database
    # Always make sure to close the connection to the database 
    # (much like you should always close a file when done with it).
    conn.close()
    
    return binary_model_id

def ingest_errs(binary_model_err_vals_and_types, binary_model_id):

    """
    Ingests error values and types into the database.
    
    Inputs:
        err_vals: A pandas DataFrame containing error values
        err_types: A pandas DataFrame containing error types
    Outputs:
        NONE - currently, will fix to show whether or not it successfully ingests the errors
    """
    info("in ingest_errs")
    cur, conn = db_connect()
    for prop, data in binary_model_err_vals_and_types.iterrows():
        cur.execute(
            """
            INSERT INTO error_values (binary_model_id, property_name, error_type, error_lower, error_upper)
            VALUES (%s, %s, %s, %s, %s);
                """,
                (binary_model_id, prop, data['Error Type'], data['error_lower'], data['error_upper'])
            )

    conn.commit()
    conn.close()

def ingest_bibliography(bib):

    """
    Ingests a biliography into the table "bibliography". Each bibliography must be associated with at least one model, and vice versa.

    Inputs:
        bib: A list-like of values corresponding to the bibliography table columns
    Outputs:
        NONE - currently, will fix to show whether or not it successfully ingests the bibliography
    """

    cur, conn = db_connect()
    
    cur.execute(
        """
        INSERT INTO bib (created_at, updated_at, doi, title, year, citations)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING bib_id;
        """,
        (bib["created"], bib["updated"], bib["doi"], bib["title"], bib["year"], bib["citations"])
    )
    
    conn.commit()
    conn.close()
    
def ingest_evidence(evidence_subcats_and_wavebands, binary_model_id):
    """
    Ingests evidence subcategories into the database.
    
    Inputs:
        evidence_subcat: A pandas DataFrame containing evidence subcategories
        binary_model_id: The ID of the binary model to associate with the evidence subcategories
    Outputs:
        The ID of the evidence subcategory that was ingested
    """
    info("in ingest_evidence")
    cur, conn = db_connect()
    for i in evidence_subcats_and_wavebands["subcat"].index:
        cur.execute(
            """
            INSERT INTO evidence_subcategories (evidence_subcategory_type)
            VALUES (%s)
            RETURNING evidence_subcategory_id;
            """,
            (evidence_subcats_and_wavebands["subcat"].iloc[i])
        )
        evidence_subcategory_id = cur.fetchone()[0]
        info(f"Inserted evidence subcategory {evidence_subcats_and_wavebands['subcat'].iloc[i]['subcategory_name']} with ID {evidence_subcategory_id}")

        cur.execute(
            """
            INSERT INTO model_evidence (binary_model_id, evidence_subcategory_id)
            VALUES (%s, %s)
            RETURNING model_evidence_id
            """,
            (binary_model_id, evidence_subcategory_id)
        )
        model_evidence_id = cur.fetchone()[0]
        info(f"Inserted model evidence {model_evidence_id} for binary model {binary_model_id} and evidence subcategory {evidence_subcategory_id}")

        for waveband in evidence_subcats_and_wavebands["waveband"].iloc[i]:
            cur.execute(
                """
                INSERT INTO model_evidence_waveband (model_evidence_id, waveband)
                VALUES (%s, %s)
                """,
                (model_evidence_id, waveband)
            )
            info(f"Inserted model evidence waveband {model_evidence_id} for waveband {waveband}")

    conn.commit()
    conn.close()
###############

###############
def ingest():

    '''.

    Ingestion of sources and models into database starting from a
    specific google spreadsheet setup.
    
    Inputs:
        N/A
    Outputs:
        statements telling you whether a source/model has been ingested into the database

    '''

    start_time = time.time()

    # Create the url to the google spreadsheet that contains the
    # source information and a possible link to a model parameter
    # extraction google spreadsheet from the key string value given
    # for using the function.
    #TODO hardcode
    url = create_url(db_info['googlekey'])
    # Pull the relativant information about the source from the google
    # spreadsheet, this includes the paper link, the name of the
    # source in NED, and a link to another google spreadsheet that
    # contains the model parameter information.  This information gets
    # put into a pandas dataframe for easy manipulation in python.

    summary_list_warnings = ["\n==========WARNINGS=========="]
    summary_list_value_filling = ["\n==========VALUE FILLING=========="]


    ingestion_data = pd.read_csv(url, usecols = ["Paper Link", "Candidate Name",  "NED Name", "Model Parameter Details"])

    failed_redshift = 0
    value_fills = 0
    name_changes = 0
    odd_params = 0
    odd_errs = 0
    
    ned_names = []
    candidate_names = []
    candidates = []
    models = pd.DataFrame(index=["paper link", "source name", "eccentricity", "log(m1)", "log(m2)", "log(total mass)", "log(chirp mass)", "log(reduced mass)", "q", "inclination", "semi-major axis", "separation", "period epoch", "orbital frequency (earth frame)", "orbital period (earth frame)", "Summary/notes on source", "Caveats", "Extension project"])

    # Go through all the different sources from the spreadsheet.
    print("Getting NED Names...")
    for i in range((len(ingestion_data))):
        # Set the ned_name variable as the information from the NED Name column.
        ned_name = ingestion_data.iloc[i,2]
        #print(ned_name)
        # If there is a ned_name given (note that it is possible some
        # candidates don't have this so think about what would need to
        # be done to account for that), get the j2000 ra and dec of
        # the source in degrees, as well as the redshift. Should
        # probably put in / use the NED name resolver function in
        # BOBcat utils at this point as well, will come back and
        # figure out exactly where in the script it should be added.
#        if ned_name:
            # Set the ra_deg and dec_deg variables to the j2000 ra and
            # dec positions given in NED for the source.

        ned_names.append(ned_name)
        candidate_names.append(ingestion_data.iloc[i,1])        
    ned_names = np.unique(ned_names)
    candidate_names = np.unique(candidate_names)

    print("Retrieving binary models...")

    # Convert ADS links to Scix links
    bibcodes = []
    for i in range(len(ingestion_data)):
        ingestion_data.iloc[i, 0], bibcode = ads_to_scix(ingestion_data.iloc[i, 0])
        bibcodes.append(bibcode)
        # TODO: Store bibcodes in database

    keys = []
    for i in range(len(ingestion_data)):
        if isinstance(ingestion_data.iloc[i,3],str): #this is checking the column for anything and converting it to strings (it could be a NaN if nothing was in the column)
            # Pull just the key of the google spreadsheet out of the link that is listed in the source spreadsheet.
            binary_model_key = ingestion_data.iloc[i,3].split("/")[5]
            #print("DEBUG: Primary model key "+binary_model_key)
            # Create the full url to the model parameter extraction spreadsheet
            binary_model_url = create_url(binary_model_key)
            if binary_model_key not in keys:
                keys.append(binary_model_key)
            else:
                raise ValueError(f"Binary model url {binary_model_url} already exists in the list of urls (duplicate sheet)!")
            #print("DEBUG: "+binary_model_url)
            # Pull the relativant information about the model from the google spreadsheet.
            # This information gets put into a pandas dataframe for easy manipulation in python.
            try:
                binary_model_info = pd.read_csv(binary_model_url, \
                    usecols = ['Name', 'Value', 'Error', 'Error type'])
            except Exception as e:
                raise SystemError(f"Unable to connect to spreadsheet {binary_model_url}\nSpecific error message: {e}")

            # Create the model array needed to use the ingest_model function. 
            # This should truly be whether a creation of an instance of the model class is put. Still currently
            # working and debugging the class code after moving it from ipython notebooks to regular script 
            # python. Will come back and fix that as soon as the model class is better situated.
        else:
            warning(f"\n!!! No parameter url in the data entry list for {ingestion_data.iloc[i,2]} !!!")

        nan_idx = binary_model_info['Name'].isna().idxmax() # Cut off the data at the first NaN name value, since below that is the templating stuff we don't want to ingest
        binary_model = binary_model_info.loc[:nan_idx-1, ['Name', 'Value']]
        binary_model.set_index('Name',inplace=True)

        # Get bib info
        bib_info = pd.DataFrame(columns=["created", "updated", "doi", "title", "year", "citations"])
        bib_info.loc[i, ["created", "updated"]] = [time.time(), time.time()] # TODO: Figure out how to make these not be the same
        bib_info.loc[i, ["title", "year", "citation"]] = [np.nan, np.nan, np.nan]
        binary_model.loc["paper link"], bib_info.loc[i, "doi"] = ads_to_scix(binary_model.loc["paper link"].values[0])

        if binary_model.loc["source name"].values[0] != ingestion_data.iloc[i,2]:
            warning(f"""
            ====================================================================================================================================================
            WARNING! Candidate NED name and model name do not match! Setting model name {binary_model.loc["source name"].values[0]} to candidate NED name {ingestion_data.iloc[i,2]}.
            ====================================================================================================================================================
            """)
            old_name = binary_model.loc["source name"].values[0]
            binary_model.loc["source name"] = ingestion_data.iloc[i,2]
            summary_list_warnings.append("Set model name "+str(old_name)+" to candidate NED name "+str(ingestion_data.iloc[i,2])+".")
            name_changes += 1
        binary_model, fills = value_filling(binary_model, summary_list_value_filling, summary_list_warnings, binary_model_url)
        if fills:
            value_fills += 1
        value_warnings, weirdness = check_binary_model(binary_model, binary_model_url)
        summary_list_warnings.extend(value_warnings)
        if weirdness:
            odd_params += 1

        models.loc[:,len(models)] = binary_model

        # Prep errors for ingestion
        # TODO: Make an error value and type checking function. Will have to make sure there is a type for every value, or the indexing will be off!
        binary_model_err_vals_and_types = pd.DataFrame(binary_model_info.iloc[:nan_idx,2], index=binary_model_info.iloc[:nan_idx,0], columns=["Error"])
        binary_model_err_vals_and_types["Error Type"] = binary_model_info.iloc[:nan_idx,3]
        binary_model_err_vals_and_types.dropna(inplace=True)
        rows_without_commas = ~binary_model_err_vals_and_types["Error"].str.contains(",", na=False)
        upper_and_lower_errs = binary_model_err_vals_and_types["Error"].str.split(",", n=1, expand=True)
        if upper_and_lower_errs.shape[1] == 2:
            binary_model_err_vals_and_types['error_lower'] = upper_and_lower_errs.iloc[:, 0].astype(float)
            binary_model_err_vals_and_types['error_upper'] = upper_and_lower_errs.iloc[:, 1].astype(float)
        elif upper_and_lower_errs.empty == True:
            binary_model_err_vals_and_types['error_lower'] = np.nan
            binary_model_err_vals_and_types['error_upper'] = np.nan
        else:
            binary_model_err_vals_and_types['error_lower'] = upper_and_lower_errs.iloc[:, 0].astype(float)
            binary_model_err_vals_and_types['error_upper'] = upper_and_lower_errs.iloc[:, 0].astype(float)
        if len(binary_model_err_vals_and_types.loc[rows_without_commas]) > 0:
            binary_model_err_vals_and_types.loc[rows_without_commas, 'error_lower'] = -1*binary_model_err_vals_and_types.loc[rows_without_commas, "Error"]
            binary_model_err_vals_and_types.loc[rows_without_commas, 'error_upper'] = binary_model_err_vals_and_types.loc[rows_without_commas, "Error"]
        binary_model_err_vals_and_types = binary_model_err_vals_and_types.drop(columns=["Error"])
        err_warnings, weirdness = check_errs(binary_model, binary_model_err_vals_and_types, binary_model_url)
        summary_list_warnings.extend(err_warnings)
        if weirdness:
            odd_errs += 1

        # Prep evidence for ingestion
        evidence_info = binary_model.loc[binary_model.index.str.contains("evidence")] # Will contain the evidence categories, subcats, and wavebands
        if len(evidence_info) % 3 != 0:
            raise ValueError(f"Incomplete evidence entry for {binary_model_url}. Evidence entries must come in groups of 3 (category, subcategory, waveband).")
        n_list = np.array([int(i) for i in range(0, len(evidence_info), 3)])
        # These will be indexed properly: subcat[0] and waveband[0] all correspond to the same evidence entry
        evidence_subcats = evidence_info.iloc[n_list + 1] # Subcat uniquely determines cat, so there's no need to save evidence_cat
        evidence_wavebands = evidence_info.iloc[n_list + 2]
        evidence_subcats_and_wavebands = pd.DataFrame(columns=["subcat", "wavebands"])
        for subcat in evidence_subcats.values:
            indices = [index for index, value in enumerate(evidence_subcats) if value == subcat]
            wavebands_for_subcat = evidence_wavebands[indices].to_numpy()
            evidence_subcats_and_wavebands.loc[len(evidence_subcats_and_wavebands), "subcat"] = subcat
            evidence_subcats_and_wavebands.loc[len(evidence_subcats_and_wavebands), "wavebands"] = wavebands_for_subcat
        evidence_subcats_and_wavebands.dropna(inplace=True)

    print("Getting other candidate parameters... This may take a while.")
    ned_retrieval_times = []
    for i in range(len(ned_names)):
        #candidate_name = ingestion_data.iloc[i,1]
        ned_start_time = time.time()
        try:
            ra, dec = (astrodb.coord_finder(ned_names[i]))
        except Exception as err:
            raise RuntimeError(f"Could not find coordinates for candidate {ned_names[i]}.")
        # Convert sky coords to degrees.
        coords = SkyCoord(ra,dec)
        ra_deg = float(coords.ra.degree)
        dec_deg = float(coords.dec.degree)
        
        info("Coordinates found for object {}: {}, {}".format(ned_names[i], ra_deg, dec_deg))
        # Set redshift variable to the redshift given in NED for the source.
        try:
            redshift, name_change = astrodb.redshift(ned_names[i])
            if name_change:
                info(f"Updated NED name for object {ned_names[i]} to {name_change} due to more complete NED entry.")
                # Change name in models to name_change wherever it occurs
                models.loc[models["source name"] == ned_names[i], "source name"] = name_change
                ned_names[i] = name_change
                candidate_names[i] = name_change
            info("Redshift found for object " + ned_names[i])
        except Exception as err:
            warning(f"Redshift not found for object {ned_names[i]}. Message from redshift query: {err}")
            summary_list_warnings.append("Redshift not found for object "+str(ned_names[i])+".")
            redshift = np.nan
            failed_redshift += 1
        if not np.isnan(redshift):
            Dl = calc.cosmo_calc(float(redshift))
        ned_end_time = time.time()
        ned_retrieval_times.append(ned_end_time-ned_start_time)

        #candidate = [candidate_name, ra_deg, dec_deg, redshift]
        candidates.append([ned_names[i], ra_deg, dec_deg, redshift, Dl, np.nan, time.time()]) # TODO: Integrate the rating system into this

    # Ingestion and additional calculated properties
    candidate_ids = pd.Series(index=np.unique(ned_names))
    candidate_Dls = pd.Series(index=np.unique(ned_names))
    for source in candidates:
        try:
            candidate_id, Dl = ingest_candidate(source)
            candidate_ids[source[0]] = candidate_id
            candidate_Dls[source[0]] = Dl
        except Exception as e:
            raise SystemError(f"Candidate not ingested: {source[0]}. Error: {e}")
        info(f"Candidate ingested: {source[0]}")

    for _, model in models.iterrows():
        try:
            bib_id = ingest_bibliography(bib_info.loc[_])
        except Exception as e:
            raise SystemError(f"Bibliography not ingested: {model.iloc[1]}. Error: {e}")
        info(f"Bibliography ingested: {model.iloc[1]}")

        # Additional calculated properties
        ###########
        h = calc.strain_calc(10**float(model["log(chirp mass)"]), float(candidate_Dls[model["source name"]]), 2*float(model["orbital frequency (earth frame)"]))
        timescale = np.nan # TODO: implement this properly
        new_model = model.copy().insert(16, "gw_strain", h)
        new_model = new_model.insert(17, "gw_timescale", timescale)
        new_model = new_model.insert(0, "created_at", time.time())
        ###########

        try:
            binary_model_id = ingest_binary_model(new_model, candidate_ids[model["source name"]], bib_id)
        except Exception as e:
            raise SystemError(f"Binary model not ingested: {model.iloc[1]}. Error: {e}")
        info(f"Binary model ingested: {model.iloc[1]}")

        try:
            ingest_errs(binary_model_err_vals_and_types, binary_model_id)
        except Exception as e:
            raise SystemError(f"Binary model errors not ingested: {model.iloc[1]}. Error: {e}")
        info(f"Binary model errors ingested: {model.iloc[1]}")

        try:
            subcat_id = ingest_evidence_subcat(evidence_subcat, binary_model_id)
        except Exception as e:
            raise SystemError(f"Binary model evidence subcategories not ingested: {model.iloc[1]}. Error: {e}")
        info(f"Binary model evidence subcategories ingested: {model.iloc[1]}")

        try:
            ingest_evidence_waveband(evidence_waveband, subcat_id)
        except Exception as e:
            raise SystemError(f"Binary model evidence wavebands not ingested: {model.iloc[1]}. Error: {e}")
        info(f"Binary model evidence wavebands ingested: {model.iloc[1]}")

    # Summary of ingestion.

    for message in summary_list_value_filling:
        print(message)
    for message in summary_list_warnings:
        print(message)
    
    end_time = time.time()
    runtime = end_time - start_time
    print(f"""
                                                                            \n==========SUMMARY==========
    Successfully ingested {len(candidates)} candidates.
    Successfully ingested {len(models)} binary models.
    Failed to find redshift for {failed_redshift} sources.
    Had to change {name_changes} names.
    Successfully filled some values for {value_fills} models ({len(models) - value_fills} failed).
    Found {odd_params} models with inconsistent/suspicious parameters.
    This all took {runtime} seconds.
    Average NED data retrieval time: {np.mean(ned_retrieval_times)} seconds. Max of {np.max(ned_retrieval_times)} seconds.
    """)






if __name__ == "__main__":
    # add parsing from command line
    # ingest.py -key asdfjasgdh -path /Users/sbs/.bobcat/db_info.txt
    #

    
    # parse user inputs and read user info from file

    # Run ingest function.

    print("DEBUG: Started the program. About to run ingest().")
    ingest()
    #ingest("1WU4c_FCEOMEmd1m_680qtqNR7rFIzNztT2GxZpX4dvk","/Users/sbs/.bobcat/db_info.txt")
