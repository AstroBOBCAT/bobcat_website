## update_m1.py has the code for the update_m1 function. This function will check to see if 
## the mass 1 value passed to the function is the same or within some tolerance to the 
## mass 1 value calculated. If there is not mass 1 value passed into the function, or the 
## tolerance is exceeded, then the calculated mass 1 value becomes the value used and 
## returned as the mass 1.


######
# Import the need libraries and modules for the function to work.
from .find_m1_m2 import find_m1_m2
######

###############
def update_m1(m1 = None, m2 = None, Mtot = None, q = None, Mc = None, mu = None, tolerance = 1e5):
    '''
    Update the mass 1 value given to that calculated if the tolerance is not met.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given, default = None
        m2 = mass of second binary object, units = same as the other mass value given, default = None
        Mtot = total mass of the system, units = same as the other mass values given, default = None
        q = mass ratio of the system, units = NA, default = None
        Mc = chirp mass of the system, units = same as the other mass values given, default = None
        mu = reduced mass of the system, units = same as the other mass values given, default = None
        tolarance = what the difference has to be less than or equal to in order to not replace
        the given value with that calculated, units = NA, default = 1e5
    
    Outputs:
        m1 = mass of first binary object, units = same as the units of the masses passed to function
    '''
    
    # Try to calculate m1 from whatever given mass values you have using the find_m1_m2 function
    try:
        m1_calced = find_m1_m2(m1, m2, Mtot, q, Mc, mu)[0]
    # If the find_m1_m2 function fails, then raise an error becuase none of the mass values can be calculated.
    except:
        raise ValueError("Not enough mass values available to calculate m1 and m2.")

    # If no m1 was passed to the function or the difference between the value passed and
    # the value calculated is greater than the tolerance, the calculated m1 value is the
    # the mass value used for m1.
    if m1 == None or abs(m1 - m1_calced) >= tolerance:
        m1 = m1_calced

    # If none of the above criteria are met then the m1 value passed to the function
    # stays as the m1 value.
    else:
        pass
    return m1
##############
