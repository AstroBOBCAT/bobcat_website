## NED_name.py contains the code for the function NED_name(). This function takes the ra and dec, in degrees,
## of an object and and quieries the NED database for the names associated with the objects that are within a 
## radius from the ra and dec passed to NED. Then the objects are sorted so that the object with the 
## smallest separation is selected. This is essentially picking out the object with ra and dec values
## closest to those passed to the function. The name of this object is returned by the function.


######
# Import the need libraries and modules for the function to work.
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.ipac.ned import Ned #needed to connect to the NED database
######


###############
def NED_name(ra, dec, radius_tol = 0.01):
    '''
    Use NED search library to determine name of nearest NED-listed galaxy
    within a narrow position search.

    Inputs:
        ra = J2000 right ascension, units = degrees
        dec = J2000 declination, units = degrees
        radius_tol = tolerance of the search radius used in the query to the NED database, units = degrees, default = 0.01
    
    Outputs:
        name = name of the object closest to the given ra and dec, units = NA
    '''

    # Check that the arugments are actually numerical, i.e. the ra and dec passed to the function
    # are in degrees.
    if isinstance(ra, (int, float)) and isinstance(dec, (int, float)):
        # Put coordinates into an array.
        coords = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg), frame='icrs')

        # Query the NED database for objects within radius_tol degrees, radially, 
        # of the chosen point (ra,dec), and creates a table.
        result_table = Ned.query_region(coords, radius=radius_tol*u.deg, equinox='J2000.0')

        # Find object closest to the center of the region and drops all other objects from the dataframe.
        result = result_table[result_table['Separation']== result_table['Separation'].min()]
        
        # Extract the name from dataframe and return it.
        name = result[0]['Object Name'] 
        return name
    
    # If the arguments are not numerical, i.e. of hmsdms, then raise an error.
    else:
        raise RuntimeError("Arguments given are incorrect. Make sure ra and dec are in degrees.")
###############
