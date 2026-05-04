## update_mu.py has the code for the update_mu function. This function will check to see if 
## the reduced mass value passed to the function is the same or within some tolerance to the 
## reduced mass value calculated given the m1 and m2. If there is not reduced mass value passed
## into the function, or the tolerance is exceeded, then the calculated reduced mass value
## becomes the value used and returned as the reduced mass.


######
# Import the need libraries and modules for the function to work.
from .mu_calculator import mu_calc
######

###############
def update_mu(m1, m2, mu = None, tolerance = 1e5):
    '''
    Update the reduced mass value given to that calculated if the tolerance is not met.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
        mu = reduced mass of the system, units = same as the other mass values given, default = None
        tolarance = what the difference has to be less than or equal to in order to not replace
        the given value with that calculated, units = NA, default = 1e5
    
    Outputs:
        mu = reduced mass of the system, units = same as the units of the masses passed to function
    '''
    
    # Calculate the reduced mass from the given m1 and m2
    mu_calced = mu_calc(m1, m2)

    # If no reduced mass was passed to the function or the difference between the value passed and
    # the value calculated is greater than the tolerance, the calculated reduced mass value is the
    # the mass value used for reduced mass.
    if mu == None or abs(mu - mu_calced) >= tolerance:
        mu = mu_calced

    # If none of the above criteria are met then the reduced mass value passed to the function
    # stays as the reduced mass value.
    else:
        pass

    return mu
##############