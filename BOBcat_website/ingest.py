from mainpage.models import source
from mainpage.models import binary_model

from decimal import Decimal


import pandas as pd
import numpy as np

from BOBcat_utils.NED_name_resolver import NED_name_resolver
from BOBcat_utils.ra_hms2deg import ra_hms2deg
from BOBcat_utils.dec_dms2deg import dec_dms2deg
from BOBcat_utils.update_m1 import update_m1
from BOBcat_utils.update_m2 import update_m2
from BOBcat_utils.update_Mc import update_Mc
from BOBcat_utils.update_Mtot import update_Mtot
from BOBcat_utils.update_mu import update_mu
from BOBcat_utils.update_q import update_q
from BOBcat_utils.update_all_masses import update_masses
from BOBcat_utils.frequency_calculator import freq_calc
from BOBcat_utils.strain_calculator import strain_calc
from BOBcat_utils.cosmology_calculator_simple import cosmo_calc


## This script is used to create the full url needed for having the information in the expected google 
## spreadsheet that is outputted into a csv file. All the function needs is the google spreadsheet key that can
## be found in the google spreadsheet link. Note that the link in the browser when you open a google
## spreadsheet will contain the key needed but it is not the correct url needed. Hence this function
## was created to make sure the url was the correct format needed.

##############
def create_url(key):

    '''Create url for a google spreadsheet such that it is in csv format given the spreadsheet key.
    
    Inputs:
        key - this is a long string of random letters and numbers found in all the links to the 
        google spreadsheet in question
        
    Outputs:
        url string
    '''

    # First we need to check that the key given is actually a string.
    # If it isn't a string we could change it into a string but it is probably better to raise an error to
    # make sure the user is aware of what is wanted for the function.
    if not isinstance(key, str):
        raise TypeError("key must be a string")

    # Concatenate the key with the needed strings. The last portion is what turns the google spreadsheet into
    # csv format which makes it very easy to read into a pandas dataframe in other functions.
    url = "https://docs.google.com/spreadsheet/ccc?key=" + key + "&output=csv"
    return url
#############


# this is the one place that you'll have to change to ingest sources from a new google sheet
url = create_url("12_WqNWCJ3pypH3gD0szNaSFOS5_pmzuWReAqu8_3voE")
print("Hello World")
print(url)
# read in the source information
source_info = pd.read_csv(url, usecols = ["Source Name", "J2000 RA (hms)", "J2000 Dec (dms)", \
                                          "Redshift", "Parameter Extraction"])
print(source_info)

# loop through all the different sources
for i in range((len(source_info))):
    # find the NED name of the source
    ned_name = NED_name_resolver(source_info.iloc[i,0])
    # see if the source is already in the data
    db_sources = source.objects.filter(NED_name = ned_name)

    # if the source isn't in the database then add it
    if len(db_sources) == 0:


        print(source_info.iloc[i,0])
        
        print(ned_name)
        ra_hms = source_info.iloc[i,1]
        dec_dms = source_info.iloc[i,2]
        redshift = source_info.iloc[i,3]
        # convert the coordinates into degrees to store as well
        ra_deg = ra_hms2deg(ra_hms)
        dec_deg = dec_dms2deg(dec_dms)
        print(ra_hms, dec_dms, ra_deg, dec_deg)

        luminosity_distance = cosmo_calc(redshift)[0]
        print(luminosity_distance)

        # create a new source instance
        new_source = source(NED_name = ned_name, ra = ra_hms, dec = dec_dms,\
                            ra_deg = ra_deg, dec_deg = dec_deg, redshift = redshift,\
                                luminosity_distance = luminosity_distance)
        # save the new source instance to the database
        new_source.save()
    # if the source is already in the database we don't need to create a source instance and save it
    else:
        print(ned_name + " is already in database")

    # get the url for the binary model parameter sheet
    model_param_key = source_info.iloc[i,4].split("/")[-2]
    print(model_param_key)

    model_param_url = create_url(model_param_key)
    # pull the binary model parameters
    binary_model_info = pd.read_csv(model_param_url, usecols = ["Name",	"Value", "Error", "Error type"], nrows = 30)
    # replace anything that wasn't filled in with None
    binary_model_info = binary_model_info.replace(np.nan, None)

    print(binary_model_info)
    # pull out the paper link
    paper_link = binary_model_info.iloc[0,1]
    # pull out the source name of the binary model
    source_name = binary_model_info.iloc[1,1]
    # convert the source name to the NED name
    source_ned_name = NED_name_resolver(source_name)
    # check to see if this exact binary model (i.e. the one in this paper for this source) is already in the database
    db_binary_models = binary_model.objects.filter(paper_link = paper_link, source_name = source_ned_name)
    # if it isn't in the database, pull all the parameters out so we can fill things in
    if len(db_binary_models) == 0:
        # numbers have a built-in if statement that changes it from a string into the right number as long as the value isn't None
        eccentricity = [lambda: None, lambda: Decimal(binary_model_info.iloc[2,1])][(binary_model_info.iloc[2,1] != None)]()
        m1 = [lambda: None, lambda: float(binary_model_info.iloc[3,1])][(binary_model_info.iloc[3,1] != None)]()
        m2 = [lambda: None, lambda: float(binary_model_info.iloc[4,1])][(binary_model_info.iloc[4,1] != None)]()
        total_mass = [lambda: None, lambda: float(binary_model_info.iloc[5,1])][(binary_model_info.iloc[5,1] != None)]()
        chirp_mass = [lambda: None, lambda: float(binary_model_info.iloc[6,1])][(binary_model_info.iloc[6,1] != None)]()
        reduced_mass = [lambda: None, lambda: float(binary_model_info.iloc[7,1])][(binary_model_info.iloc[7,1] != None)]()
        q = [lambda: None, lambda: float(binary_model_info.iloc[8,1])][(binary_model_info.iloc[8,1] != None)]()
        evid_type_1 = binary_model_info.iloc[9,1]
        evid_type_1_note = binary_model_info.iloc[10,1]
        evid_type_1_waveband = binary_model_info.iloc[11,1]
        evid_type_2 = binary_model_info.iloc[12,1]
        evid_type_2_note = binary_model_info.iloc[13,1]
        evid_type_2_waveband = binary_model_info.iloc[14,1]
        evid_type_3 = binary_model_info.iloc[15,1]
        evid_type_3_note = binary_model_info.iloc[16,1]
        evid_type_3_waveband = binary_model_info.iloc[17,1]
        evid_type_4 = binary_model_info.iloc[18,1]
        evid_type_4_note = binary_model_info.iloc[19,1]
        evid_type_4_waveband = binary_model_info.iloc[20,1]
        inclination = [lambda: None, lambda: float(binary_model_info.iloc[21,1])][(binary_model_info.iloc[21,1] != None)]()
        semi_major_axis = [lambda: None, lambda: float(binary_model_info.iloc[22,1])][(binary_model_info.iloc[22,1] != None)]()
        separation = [lambda: None, lambda: float(binary_model_info.iloc[23,1])][(binary_model_info.iloc[23,1] != None)]()
        period_epoch = [lambda: None, lambda: float(binary_model_info.iloc[24,1])][(binary_model_info.iloc[24,1] != None)]()
        orb_freq = [lambda: None, lambda: float(binary_model_info.iloc[25,1])][(binary_model_info.iloc[25,1] != None)]()
        orb_period = [lambda: None, lambda: float(binary_model_info.iloc[26,1])][(binary_model_info.iloc[26,1] != None)]()
        gw_freq = [lambda: None, lambda: float(binary_model_info.iloc[25,1])][(binary_model_info.iloc[25,1] != None)]()
        summary = binary_model_info.iloc[27,1]
        caveats = binary_model_info.iloc[28,1]
        ext_projects = binary_model_info.iloc[29,1]

        # update the mass values
        new_masses, masses_that_changed = update_masses(m1, m2, total_mass, q, chirp_mass, reduced_mass)
        #print(old_masses)
        #print(new_masses)
        #print(masses_that_changed)
        m1 = new_masses[0]
        m2 = new_masses[1] 
        total_mass = new_masses[2] 
        q = new_masses[3]
        chirp_mass = new_masses[4]
        reduced_mass = new_masses[5]

        # find the gw info if possible (mainly for plotting purposes but still okay to put in the database)
        orb_period, orb_freq, gw_freq = freq_calc(orb_period, orb_freq, gw_freq)
        assoicated_source = source.objects.filter(NED_name = source_ned_name).values("luminosity_distance")[0]
        luminosity_distance = assoicated_source["luminosity_distance"]
        print(float(luminosity_distance))
        print(float(gw_freq))
        gw_strain = strain_calc(float(chirp_mass),float(luminosity_distance),float(gw_freq))
        print(gw_strain)


        # make a new binary model instance to store in the database
        new_binary_model = binary_model(
            paper_link = paper_link,
            source_name = source_ned_name,
            eccentricity = eccentricity,
            m1 = m1,
            m2 = m2,
            total_mass = total_mass,
            chirp_mass = chirp_mass,
            reduced_mass = reduced_mass,
            q = q, 
            evid_type_1 = evid_type_1.replace("_", " "),
            evid_type_1_note = evid_type_1_note,
            evid_type_1_waveband = evid_type_1_waveband,
            evid_type_2 = evid_type_2,
            evid_type_2_note = evid_type_2_note,
            evid_type_2_waveband = evid_type_2_waveband,
            evid_type_3 = evid_type_3,
            evid_type_3_note = evid_type_3_note,
            evid_type_3_waveband = evid_type_3_waveband,
            evid_type_4 = evid_type_4,
            evid_type_4_note = evid_type_4_note,
            evid_type_4_waveband = evid_type_4_waveband,
            inclination = inclination,
            semi_major_axis = semi_major_axis,
            separation = separation,
            period_epoch = period_epoch,
            orb_freq = orb_freq,
            orb_period = orb_period,
            summary = summary,
            caveats = caveats,
            ext_projects = ext_projects

        )

        new_binary_model.save()

        print(paper_link)
        print(m1)
    # if the exact binary model is already in the database we don't need to do the above
    else:
        print("binary model is already in the database")




