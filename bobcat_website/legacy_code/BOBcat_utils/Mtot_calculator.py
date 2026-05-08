## Mtot_calculator.py holds the code for the function Mtot_calc(). This function will calculate
## the total mass of a system given the two masses within the system. It uses the equation
## m1+m2


#############
def Mtot_calc(m1,m2):
    '''
    Calculate the total mass of a system given two masses.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
    
    Outputs:
        Mtot = total mass of the system, units = same as the units of the masses passed to function
    '''
    
    return float(m1)+float(m2)
##############
  