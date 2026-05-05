## q_calculator.py holds the code for the function q_calc(). This function will calculate
## the mass ratio of a system given the two masses within the system. It uses the equation
## m(smaller)/m(bigger) so that q is always between 0 and 1.


##################
def q_calc(m1,m2):
    '''
    Calculate the mass ratio of a system given two masses.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
    
    Outputs:
        q = mass ratio of the system, units = NA
    '''

    # Check to see if m1>m2, which is what we want to force so that q remains between 0 and 1.
    if m1 > m2:
        return m2/m1 
    # If m2>m1 then we just change the ratio so that q is still between 0 and 1.
    else:
        return m1/m2
###################