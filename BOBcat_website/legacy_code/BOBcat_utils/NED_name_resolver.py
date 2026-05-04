## NED_name_resolver.py contains code for the NED_name_resolver() funciton. This function allows the user
## to enter an name of an astronomical object and get back the first name associated with the object
## in the NED database. This is useful as there are many different naming schemes through astronomy
## and the results are that most objects have multiple names. The "NED name" that is returned from the
## function is just the first name in the list of names NED has associated with it. This is not a complete
## fail safe as there are some naming schemes or objects' names that aren't in the NED database even if the
## actual object is. 


######
# Import the need libraries and modules for the function to work.
from astroquery.ipac.ned import Ned #allows the connection to the NED database
from .coordinate_finder import coord_finder
from .coordinate_converter import coord_converter
from .NED_name import NED_name
######

###################
def NED_name_resolver(name):
    ''' 
    Take an astronomical object's name and return the associated NED name for the object.
     
    Inputs:
        name string of astronomical object
    Outputs:
        NED name (or the first name in the list of names) for the astronomical object
    '''

    # First we need to check that the name given is actually a string.
    # If it isn't a string we could change it into a string but it is probably better to raise an error to
    # make sure the user is aware of what is wanted for the function.
    if not isinstance(name, str):
        raise TypeError("Name must be a string.")

    # Try to find the name in the NED database.
    try:

        # Query the NED database for the object based on the name passed to the function.
        #result_table = Ned.query_object(name) #### This code seems to have weird things happening to it.
        #### Like it'll give me normal results for "3c66b" but completely different and werid results when I
        #### give it "3C66B". It also was except "sam", "abs", "asfsd", and other things that definitely
        #### aren't in the NED database.
        ra, dec = coord_finder(name)

        # Convert ra and dec from hmsdms to degrees.
        ra_deg, dec_deg = coord_converter(ra, dec)

        # Pull just the object's name out of the table (stripping the extra white spaces).
        #NED_name = str(result_table['Object Name']).replace('Object Name\n-----------\n', '').strip()
        res_name = NED_name(ra_deg, dec_deg)

        # Return the NED name
        return (res_name)
    # If the name is not in the NED database then raise an error. (There will most likely be another error raised 
    # by the NED query failing that says the same thing).
    except:
        raise SystemError("Name given is not in NED database.")
##################