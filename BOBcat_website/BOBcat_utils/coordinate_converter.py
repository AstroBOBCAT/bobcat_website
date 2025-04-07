## coordinate_converter.py contains the code for the coord_converter function. This function allows you to 
## convert the coordinates from J2000 ra and dec in the units of hmsdms to J2000 ra and dec in the units of 
## degrees. 


######
# Import the need libraries and modules for the function to work.
import numpy as np
from astropy.coordinates import SkyCoord 
######


####################
def coord_converter(ra, dec): 
    '''
    Convert J2000 ra and dec with units of hmsdms into J2000 ra and dec with units of degrees.

    Inputs:
        ra = J2000 right ascension, units = hms
        dec = J2000 declination, units = dms 

    Outputs:
        ra = J2000 right ascension, units = degrees
        dec = J2000 declination, units = degrees
    '''

    # Make sure the ra and dec passed to the function are strings, i.e. they're most likely in hmsdms units. 
    # If not raise an error.
    if not isinstance(ra, str) or not isinstance(dec, str):
        raise TypeError("ra and dec must be strings.")
    
    # Try to convert the coordinates into decimal degrees.
    try:
        # Convert the coordinates into degrees.
        coords_arr = SkyCoord(ra, dec)

        # Split the ra and dec and return them.
        ra_deg, dec_deg = np.array([coords_arr.ra.degree, coords_arr.dec.degree]) 
        return ra_deg, dec_deg
    # If something goes wrong in the above code block it is most likely because the ra and dec passed to the 
    # function weren't entered exactly correctly. Therefore, raise an error.
    except:
        raise SystemError("Make sure ra and dec are entered correctly.")
######################