## mu_calculator.py holds the code for the function mu_calc(). This function will calculate
## the reduced mass of a system given the two masses within the system. It uses the equation
## (m1*m2)/(m1+m2)


#############
def mu_calc(m1,m2):
    '''
    Calculate the reduced mass of a system given two masses.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
    
    Outputs:
        mu = reduced mass of the system, units = same as the units of the masses passed to function
    '''
    
    return (m1*m2)/(m1+m2) 
############     