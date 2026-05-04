## update_Mtot.py has the code for the update_Mtot function. This function will check to see if 
## the total mass value passed to the function is the same or within some tolerance to the 
## total mass value calculated given the m1 and m2. If there is not total mass value passed
## into the function, or the tolerance is exceeded, then the calculated total mass value
## becomes the value used and returned as the total mass.


######
# Import the need libraries and modules for the function to work.
from .Mtot_calculator import Mtot_calc
######

###############
def update_Mtot(m1, m2, Mtot = None, tolerance = 1e5):
    '''
    Update the total mass value given to that calculated if the tolerance is not met.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
        Mtot = total mass of the system, units = same as the other mass values given, default = None
        tolarance = what the difference has to be less than or equal to in order to not replace
        the given value with that calculated, units = NA, default = 1e5
    
    Outputs:
        Mtot = total mass of the system, units = same as the units of the masses passed to function
    '''
    
    # Calculate the total mass from the given m1 and m2
    Mtot_calced = Mtot_calc(m1, m2)

    # If no total mass was passed to the function or the difference between the value passed and
    # the value calculated is greater than the tolerance, the calculated total mass value is the
    # the mass value used for total mass.
    if Mtot == None or abs(Mtot - Mtot_calced) >= tolerance:
        Mtot = Mtot_calced

    # If none of the above criteria are met then the total mass value passed to the function
    # stays as the total mass value.
    else:
        pass
    return Mtot
##############