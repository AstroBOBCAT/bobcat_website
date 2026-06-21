# General requirements
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad
from astroquery.ipac.ned import Ned
from astroquery.simbad import Simbad
from astropy.coordinates import name_resolve
from astropy.table import Table
import numpy as np
import requests

# Handling NED server time-outs
import time
import socket
from logging import warning
from logging import info
from astroquery.ipac.ned import Conf as NedConf
from astroquery.exceptions import RemoteServiceError

'''.

Wrappers that call the NASA Extragalactic Database and other repositories

# Note: the code for the timeout exception handling was initially
# written by Claude Sonnet 4.6, which produced a bunch of clunky code
# with some odd decisions. It was subsequently line-by-line verified /
# heavily changed and tested by Sarah.

'''


# ---------------------------------------------------------------------------
# NED HELPER FUNCTIONS.
# ---------------------------------------------------------------------------

def _is_timeout_exception(exc):
    """.

    Check if a timeout exception is returned.

    This checks for various sorts of timeoout errors. Others may need
    to be added if NED changes its ways.

    Input: Exception.
    Output: Boolean.

    """
    return isinstance(exc, (
        TimeoutError,                          # built-in, per astroquery API spec
        requests.exceptions.ReadTimeout,       # requests library – most common in practice
        requests.exceptions.ConnectTimeout,    # requests library – connection phase
        requests.exceptions.ConnectionError,   # requests library – connection phase
    ))

def ned_timeout(func, *args, **kwargs):
    """.

    Wrapper to handle potential time-out issues with NED for any query
    type. *** UNFORTUNATELY THE INCREASING TIMEOUT DOES NOT WORK
    AS-IS. NEEDS FURTHER INVESTIGATION. ***

    In principle, a similar format could be used for other systems'
    queries as needed.
    
    Input:
    func     = The NED query function to call (e.g. Ned.query_object, Ned.query_region).
    *args    = Positional arguments to pass to func (e.g. object_name)
    **kwargs = Keyword arguments to pass to func (e.g. radius=0.5 * u.arcmin in query_region)

    Output: The raw results of the NED query (astropy Table or
            similar), or None if the object was not found.

    Example query:
    result_table = ned_timeout(Ned.query_object, object_name)

    """

    # Pause between query re-tries; avoid overloading.
    RETRY_PAUSE_SECONDS = 10

    # Sequence of timeout values (seconds) to apply on successive attempts:
    #   attempt 1, 60 s  (first retry after an initial timeout, this is NED standard length)
    #   attempt 2, 120 s (second retry)
    #   attempt 3, 180 s (subsequent retries)
    TIMEOUT_SEQUENCE = [60, 120, 180]
    
    for i in range(len(TIMEOUT_SEQUENCE)):
        timeout_secs = TIMEOUT_SEQUENCE[i]
        NedConf.timeout = timeout_secs
        try:
            results = func(*args, **kwargs)
        except RemoteServiceError as exc:
            if "no object found" in str(exc).lower() or "not found" in str(exc).lower():
                return None
            raise RuntimeError(
                f"NED query failed with a service error: {exc}"
            ) from exc
        except Exception as exc:
            if _is_timeout_exception(exc):
                print(
                    f"[NED] Timeout on attempt {i+1} "
                    f"(timeout was {timeout_secs} s)."
                )
                if i < len(TIMEOUT_SEQUENCE) - 1:
                    new_timeout = TIMEOUT_SEQUENCE[i + 1]
                    print(
                        f"Waiting {RETRY_PAUSE_SECONDS} s then retrying "
                        f"with timeout={new_timeout} s …"
                    )
                    time.sleep(RETRY_PAUSE_SECONDS)
                    print(f"Currently retrying with timeout={new_timeout} s.")
                    continue
                else:
                    print("That was the last try and it was unsuccessful. Goodbye.")
                    raise RuntimeError(
                        f"NED query failed with a timeout error after "
                        f"{len(TIMEOUT_SEQUENCE)} attempts. NED might be down, try again later."
                    )
            raise RuntimeError(
                f"NED query failed with an unexpected error: {exc}"
            ) from exc

        # Indicate success if a timeout occurred.
        if i > 0:
            print("Success!")
        return results



def clear_ned_cache():
    '''.

    Cache clear as suggested by
    https://astroquery.readthedocs.io/en/latest/ipac/ned/ned.html#reference-api

    Always call this function before running ingest. It will prevent
    repeated failed queries or bad/out-of-date results if we've been
    running for a long time.

    '''

    Ned.clear_cache()

    return




# ---------------------------------------------------------------------------
# QUERY FUNCTIONS.
# ---------------------------------------------------------------------------

def ned_name(object_name):
    """.
    
    Query NED for an object by name and return the preferred NED
    identifier.

    Note on errors: NED itself raises an error if object is not
    identified in the database.

    Input: 
        object_name = The name of the object to query.

    Output:
        ned_name = The preferred NED object name, or errors out if name not found.

    """

    result_table = ned_timeout(Ned.query_object, object_name)

    ned_name = str(result_table["Object Name"][0])

    return ned_name


def coord_finder(object_name):
    '''.
    
    Query CDS SESAME using object_name to return its J2000 ra and dec,
    if object is found.

    Inputs:
        object_name = string of the name of the object the coordinates
                      are needed for. Name must be resolvable by
                      standard astro name query.

    Outputs:
        ra = J2000 right ascension, units = hms
        dec = J2000 declination, units = dms

    '''

    # Basic user error check: name should be a string.
    if not isinstance(object_name, str):
        raise TypeError("coord_finder: Name must be a string.")

    # Search for the coordinates of the object given the name. 
    try:
        coords = SkyCoord.from_name(object_name).to_string('hmsdms').split()
    except Exception as err:
        raise RuntimeError(f"Object {object_name} is not recognized by SESAME.")
    
    # Assign the ra and dec variables.
    ra = coords[0]
    dec = coords[1]
    
    # Return an array of the ra and dec. They are hms/dms strings.
    return ra, dec
    

def ned_name_from_position(ra, dec, radius = 0.01):
    '''.

    NOTE THIS FUNCTION IS DANGEROUS FOR CROWDED FIELDS OR OBJECTS WITH
    MULTIPLE "CHILD" IDENTIFICATIONS. Consider in the future using the
    SIMBAD parent/child relationships (if possible) to forcibly
    identify the parent of the nearest object in the region.
    
    Use NED search library to determine name of nearest NED-listed
    galaxy within a narrow position search. 

    Inputs:

        ra = J2000 right ascension, units = degrees

        dec = J2000 declination, units = degrees

        radius = tolerance of the search radius used in the query
                     to the NED database, units = degrees, default =
                     0.01
    
    Outputs:

        ned_name = name of the object closest to the given ra and dec (string)

    '''

    # If search radius too big, it will almost certainly result in a timeout.
    if (radius >= 1):
        raise RuntimeError(f"ERROR: Your requested NED search radius {radius} deg is >=1 deg. This will certainly end in a timeout. Please try again with a smaller radius.")

    # Put coordinates into an array.
    coords = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')

    # Query NED
    result_table = ned_timeout(Ned.query_region,coords,radius = radius * u.deg, equinox = 'J2000.0')

    # Find closest object, drop other objects.
    result = result_table[result_table['Separation']== result_table['Separation'].min()]
        
    # Extract the name from dataframe and return it.
    ned_name = str(result[0]['Object Name'])
    return ned_name


def redshift(object_name):

    '''
    Return redshift of object_name from NED query.

    Inputs:
        ned_name = NED name of the object
    
    Outputs:
        z = redshift of the object
    '''

    result_table = ned_timeout(Ned.query_object, object_name)
    if len(result_table) > 0:
        z = float(result_table['Redshift'][0])
    else:
        z = np.nan

    if np.isnan(z):
        warning(f"Redshift not available in NED for known object {object_name}. Expanding search to alternate names in SIMBAD.")
        try:
            alt_names = Simbad.query_objectids(object_name) # Get alternative names from SIMBAD
            print(f"For {object_name} I found alternative names {alt_names}.")
        except Exception as e:
            warning(f"Failed to query SIMBAD for object {object_name}: {e}")
        for name in alt_names:
            try:
                z = np.nan
                result_table = ned_timeout(Ned.query_object, name) # Iterate through the list of alternate names to see if any of them are listed incorrectly as separate objects in NED.
                if len(result_table) > 0:
                    z = float(result_table['Redshift'][0])
                    info(f"Redshift found for object {object_name} with alternate name {name}: {z}")
                    return z, name[0]
                else:
                    warning(f"No redshift found for object {object_name} with alternate name {name}")
            except Exception as e:
                warning(f"Failed to query NED for object {object_name} with alternate name {name}: {e}")
        if np.isnan(z):
            raise RuntimeError(f"Redshift not available in NED for object {object_name} or any of its alternate names.")


    return z, False




def name_resolver():
    '''.

    CAN WE MAKE AN INTERNAL "BOBCAT NAME" CHECKER FUNCTION???
    LIKE MAYBE OUR OWN INTERNAL LIST OF MAIN AND PET NAMES BEFORE
    ASKING NED? --- something to consider for the future.

    '''

#------------------------------------------------
