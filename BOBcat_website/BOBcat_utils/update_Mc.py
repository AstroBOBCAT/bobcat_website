## update_Mc.py has the code for the update_Mc function. This function will check to see if 
## the chirp mass value passed to the function is the same or within some tolerance to the 
## chirp mass value calculated given the m1 and m2. If there is not chirp mass value passed
## into the function, or the tolerance is exceeded, then the calculated chirp mass value
## becomes the value used and returned as the chirp mass.


######
# Import the need libraries and modules for the function to work.
from .Mc_calculator import Mc_calc
######

###############
def update_Mc(m1, m2, Mc = None, tolerance = 1e5):
    '''
    Update the chirp mass value given to that calculated if the tolerance is not met.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
        Mc = chirp mass of the system, units = same as the other mass values given, default = None
        tolarance = what the difference has to be less than or equal to in order to not replace
        the given value with that calculated, units = NA, default = 1e5
    
    Outputs:
        Mc = chirp mass of the system, units = same as the units of the masses passed to function
    '''
    
    # Calculate the chirp mass from the given m1 and m2
    Mc_calced = Mc_calc(m1, m2)

    # If no chirp mass was passed to the function or the difference between the value passed and
    # the value calculated is greater than the tolerance, the calculated chirp mass value is the
    # the mass value used for chirp mass.
    if Mc == None or abs(Mc - Mc_calced) >= tolerance:
        Mc = Mc_calced

    # If none of the above criteria are met then the chirp mass value passed to the function
    # stays as the chirp mass value.
    else:
        pass
    return Mc
##############