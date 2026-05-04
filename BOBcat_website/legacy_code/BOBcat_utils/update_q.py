## update_q.py has the code for the update_q function. This function will check to see if 
## the mass ratio value passed to the function is the same or within some tolerance to the 
## mass ratio value calculated given the m1 and m2. If there is not a mass ratio value passed
## into the function, or the tolerance is exceeded, then the calculated mass ratio value
## becomes the value used and returned as the mass ratio.


######
# Import the need libraries and modules for the function to work.
from .q_calculator import q_calc
######

###############
def update_q(m1, m2, q = None, tolerance = 0.01):
    '''
    Update the mass ratio value given to that calculated if the tolerance is not met.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
        q = mass ratio of the system, units = NA, default = None
        tolarance = what the difference has to be less than or equal to in order to not replace
        the given value with that calculated, units = NA, default = 0.01
    
    Outputs:
        q = mass ratio of the system, units = NA, default = None
    '''
    
    # Calculate the mass ratio from the given m1 and m2
    q_calced = q_calc(m1, m2)

    # If no mass ratio was passed to the function or the difference between the value passed and
    # the value calculated is greater than the tolerance, the calculated mass ratio value is the
    # the value used for mass ratio.
    if q == None or abs(q - q_calced) >= tolerance:
        q = q_calced

    # If none of the above criteria are met then the mass ratio value passed to the function
    # stays as the mass ratio value.
    else:
        pass

    return q
##############

