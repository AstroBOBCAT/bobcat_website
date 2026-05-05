## Mc_calculator.py holds the code for the function Mc_calc(). This function will calculate
## the chirp mass of a system given the two masses within the system. It uses the equation
## (((m1*m2)**3)/(m1+m2))**(1/5)


#############
def Mc_calc(m1,m2):
    '''
    Calculate the chirp mass of a system given two masses.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
    
    Outputs:
        Mc = chirp mass of the system, units = same as the units of the masses passed to function
    '''
    
    return (((m1*m2)**3)/(m1+m2))**(1/5)
##############
