import numpy as np 
import math
from astropy.coordinates import SkyCoord 
from pandas import isnull


""".

BOBcat calc library

Basic calculators and self-consistency checks for binary black hole
orbital parameters and basic (far-field limit) gravitational wave
properties.


"""


###########################
#  MASS CALCULATIONS
###########################

""".

find_m1_m2() takes in all six mass values used to describe a binary
system. From any two out of the six values, m1 and m2 can be found. We
prioritize m1 and m2 values because calculating any of the other four
mass values is easiest from m1 and m2. Therefore, this function will
determine which two (minimum) mass values were passed to it and then
calculate m1 and m2 from there. The elif statements are put in an
order such that the easiest calculations are put at the beginning and
should complete first. This means if more than two mass values are
passed to the function, the simplest calculations will occur to find
m1 and m2 values.

"""

##################

def find_m1_m2(m1 = None, m2 = None, Mtot = None, q = None, Mc = None, mu = None):
    '''.

    Find the values of m1 and m2 for a binary system given at
    least two of the six common mass parameters, i.e. a minimum of two
    values from m1, m2, Mtot, q, Mc, and mu are needed to calculate m1
    and m2.

    Inputs:

        m1 = mass of first binary object, units are same as the other
             mass value given, default = None
    
        m2 = mass of second binary object, units = same as the other
             mass value given, default = None

        Mtot = total mass of the system, units = same as the other
               mass values given, default = None

        q = mass ratio of the system, units = NA, default = None

        Mc = chirp mass of the system, units = same as the other mass
             values given, default = None

        mu = reduced mass of the system, units = same as the other
             mass values given, default = None
    
    Outputs:

        m1 = mass of first binary object, units = same as the units of
             the masses passed to function

        m2 = mass of second binary object, units = same as the units
             of the masses passed to function

    '''
    try:
        m1 = 10**m1
    except:
        pass
    try:
        m2 = 10**m2
    except:
        pass
    try:
        Mtot = 10**Mtot
    except:
        pass
    try:
        Mc = 10**Mc
    except:
        pass
    try:
        mu = 10**mu
    except:
        pass
    # Check if m1 and m2 are actually passed to the function. If they are then we can skip the remaining 
    # code and just pass them back.
    if m1!=None and m2!=None:
        pass
    
    # If we have either m1 or m2 and Mtot, the other m1 or m2 can be found easily. Mtot = m1 + m2
    elif m1!=None and Mtot!=None:
        m2 = Mtot-m1
    elif m2!=None and Mtot!=None:
        m1 = Mtot-m2

    # If we have either m1 or m2 and q, the other m1 or m2 can be found easily. q = m2/m1
    elif m1!=None and q!=None:
        m2 = q*m1
    elif m2!=None and q!=None:
        m1 = m2/q

    # If we have both q and mu, we can easily find m1 and m2.
    elif q!=None and mu!=None:
        m1 = mu*(q+1)/q 
        m2 = mu*(q+1)

    # If we have either m1 or m2 and mu, the other m1 or m2 can be found easily. mu = (m1*m2) / (m1+m2)
    elif m1!=None and mu!=None:
        m2 = (mu*m1)/(m1-mu)
    elif m2!=None and mu!=None:
        m1 = (mu*m2)/(m2-mu)

    # If we have both Mtot and q, we can find m1 and m2 easily.
    elif Mtot!=None and q!=None:
        m1 = Mtot/(q+1)
        m2 = (q*Mtot)/(q+1)

    # If we have both q and Mc, we can rearrange their equation to easily find m1 and m2.
    elif q!=None and Mc!=None:
        m1 = Mc*((q+1)/q**3)**(1/5)
        m2 = Mc*((q+1)*q**2)**(1/5)

    # If we have both Mtot and mu, we can rearrange their equations to find m1 and m2.
    elif Mtot!=None and mu!=None:
        m1 = (1/2)*(Mtot + (Mtot**2 - 4*(Mtot*mu))**(1/2))
        m2 = (1/2)*(Mtot - (Mtot**2 - 4*(Mtot*mu))**(1/2))

    # If we have Mc and mu, we can rearrange their equations to find m1 and m2.
    elif Mc!=None and mu!=None:
        m1 = mu*(1 + ((Mc**(5/2)-mu**(3/2))/(mu**(3/2))))
        m2 = mu*(1 + (mu**(3/2)/(Mc**(5/2)-mu**(3/2))))

    # If we have both Mtot and Mc, we can rearrange their equations to find m1 and m2.
    # There is an additional limit of Mc<=(0.43527528165*Mtot) which will prevent the 
    # calculator from outputting complex numbers by ensuring the chirp mass is in 
    # agreement with the total mass first. If they do not agree, the calculator will cut to the error.
    elif Mtot!=None and Mc!=None and Mc<=(0.43527528165*Mtot): 
        m1 = (1/2)*(Mtot + (Mtot**2 - 4*(Mtot*(Mc**5))**(1/3))**(1/2))
        m2 = (1/2)*(Mtot - (Mtot**2 - 4*(Mtot*(Mc**5))**(1/3))**(1/2))

    # If we have Mc and Mtot but Mc doesn't follow the restriction given to if by the Mtot,
    # then raise an error.
    elif Mc!=None and Mtot!=None and Mc>=(0.43527528165*Mtot):
            raise RuntimeError("Chrip mass too large to be correct, please check") 

    # If we have either m1 or m2 and Mc, the other m1 or m2 can be found be rearranging the chirp mass equation.
    # However, the equation involves several radicals, so as values of Mc get further from the actual (given m1),
    # there will be an increasingly larger complex portion. However, this portion is typically small,
    # and so this ".real" simply deletes the complex part so calculations can continue as normal.
    # This is currently the best way we can get around this odd part of calculations.
    elif m1!=None and Mc!=None:
        m2 = (((2/3)**(1/3))*(Mc**5))/(((9*(Mc**5)*(m1**7))+(3*((27*(Mc**10)*(m1**14))-(4*(Mc**15)*(m1**9))))**(1/2))**(1/3)) + (((9*(Mc**5)*(m1**7))+(3*((27*(Mc**10)*(m1**14))-(4*(Mc**15)*(m1**9))))**(1/2))**(1/3))/(((18)**(1/3))*(m1**3))
        m2 = round(m2.real, 16)
    elif m2!=None and Mc!=None:
        m1 = (((2/3)**(1/3))*(Mc**5))/(((9*(Mc**5)*(m2**7))+(3*((27*(Mc**10)*(m2**14))-(4*(Mc**15)*(m2**9))))**(1/2))**(1/3)) + (((9*(Mc**5)*(m2**7))+(3*((27*(Mc**10)*(m2**14))-(4*(Mc**15)*(m2**9))))**(1/2))**(1/3))/(((18)**(1/3))*(m2**3))
        m1 = round(m1.real, 16)

    # If we don't have at least two mass parameters we need to raise error for the function.
    else:
        raise RuntimeError("Not enough mass parameters to calculate m1 and m2. Need at least two mass values.")

    # Before returning m1 and m2, we want to make sure q will be betweeon 0 and 1 so we check if we
    # need to switch them or not.
    if m1!=None and m2!=None and m2 > m1:
        m1, m2 = m2, m1
    else:
        pass

    # Finally return m1 and m2 values.
    return m1, m2



def Mc_calc(m1,m2):
    '''.

    Calculate the chirp mass of a system given two masses.

    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given
    
    Outputs:

        Mc = chirp mass of the system, units = same as the units of
             the masses passed to function

    '''
    m1 = 10**m1
    m2 = 10**m2
    Mc_lin = (((m1*m2)**3)/(m1+m2))**(1/5)
    Mc = np.log10(Mc_lin)
    return Mc



def Mtot_calc(m1,m2):
    '''.

    Calculate the total mass of a system given two masses.

    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given
    
    Outputs:

        Mtot = total mass of the system, units = same as the units of
               the masses passed to function

    '''
    m1 = 10**m1
    m2 = 10**m2
    Mtot_lin = m1+m2
    Mtot = np.log10(Mtot_lin)
    return Mtot
  
def mu_calc(m1,m2):
    '''.
    
    Calculate the reduced mass of a system given two masses.

    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given
    
    Outputs:

        mu = reduced mass of the system, units = same as the units of
             the masses passed to function
    
    '''
    
    m1 = 10**m1
    m2 = 10**m2
    mu_lin = (m1*m2)/(m1+m2)
    mu = np.log10(mu_lin)
    return mu



def q_calc(m1,m2):
    '''.

    Calculate the mass ratio of a system given two masses.
    Mass ratio is here defined 0 < q <= 1

    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given
    
    Outputs:

        q = mass ratio of the system, units = N/A

    '''

    # Check to see if m1>m2, which is what we want to force so that q
    # remains between 0 and 1.
    m1 = 10**m1
    m2 = 10**m2

    if m1 > m2:
        q = m2/m1
        return q
    # If m2>m1 then we just change the ratio so that q is still
    # between 0 and 1.
    else:
        q = m1/m2
        return q



def q_limit(Mc,Mtot):
    '''.

    Code to save you from ever again having to do the quadratic equation
    while converting a pair of Mc and Mtot to a mass ratio.

    Go in peace.

    Calculate the mass ratio of a system given two masses.
    Mass ratio is here defined 0 < q <= 1

    Inputs:

        Mc = chirp mass upper limit derived from search. units are same as the other
             mass value given

        Mtot = total mass of SMBH binary. units are same as the other
             mass value given
    
    Outputs:

        q = mass ratio of the system, units = N/A

    '''
    Mc = 10**Mc
    Mtot = 10**Mtot

    term1 = math.sqrt(
        ((Mtot**4) * ((Mc/Mtot)**(2/3)))
        -
        (4* (Mc**2) * (Mtot**2) * (Mc/Mtot)**(1/3))
    )
    
    term2 = 2* (Mc**2)

    term3 = (Mtot**2) * ((Mc/Mtot)**(1/3))

    term4 = 2 * (Mc**2)

    qplus = (term1 - term2 + term3)/term4

    qminus = (-1*term1 - term2 + term3)/term4

    if (Mc/Mtot > 0.435275282):
        print("\n\t------- ERROR -------\nThe inputs you provided imply a mass ratio of q > 1\n(in other words, Mc is too big compared to Mtot).\n\nRemember q is defined 0 < q < 1. Please check your values and try again.\n\nIf you are inputing the results from a CW upper-limit run, this result implies your results are not constraining on q.\n\t---------------------\n")
        exit()

    if (qplus>qminus):
        q = qminus
        multiplier = qplus
    else:
        q = qplus
        multiplier = qminus
        

    return q,multiplier




    

# This is the BOBcat SMBHB Candidate Mass Value Calculator. It will
# read provided inputs of mass quantities and can calculate unknown
# mass quantities.  Currently, the BOBcat Mass Value Calculator is
# equipped to calculate Mass 1, Mass 2, Total Mass, Mass Ratio, Chirp
# Mass, and Reduced Mass.


#THE MASS CALCULATING FUNCTION:


# As of right now, this calculator only fills in empty values, and
# cannot be a judge of erroneous/incongruent inputs.  If the inputs
# were found via different methods/models, try entering only the inputs
# that used a consistent model.


def mass_val_calc(m1 = None, m2 = None, Mtot = None, Mc = None, mu = None, q = None): #creating the function, reading the collection of inputs
    """.

    This is the BOBcat SMBHB mass value calculator! It will calculate
    estimates of Mass 1, Mass 2, Total Mass, Mass Ratio, Chirp Mass,
    and Reduced Mass (in solar masses) given known mass parameters of
    the binary candidate (in solar masses).  To successfully calculate
    the unknown values, at least two known parameters are needed as
    inputs.

    Choose two of any inputs from the list below.
    All values below are the outputs.
    Units for all: Solar Masses
    
    m1 = Larger Mass    
    m2 = Smaller Mass
    Mtot = Total Mass
    q = Mass Ratio
    Mc = Chirp Mass
    mu = Reduced Mass

    """
    mass_array = [m1, m2, Mtot, Mc, mu, q]

    none_counter = 0

    if isnull(m1):
        none_counter+=1
    if isnull(m2):
        none_counter+=1
    if isnull(Mtot):
        none_counter+=1
    if isnull(q):
        none_counter+=1
    if isnull(Mc):
        none_counter+=1
    if isnull(mu):
        none_counter+=1
    
    if none_counter > 5:
        print("At least two of the inputs must be known to calculate the other values.")
        return mass_array
    
    mass_array, updated_masses = update_masses(m1, m2, Mtot, Mc, mu, q)


    return mass_array 



## update_m1.py has the code for the update_m1 function. 


###############
def update_m1(m1 = None, m2 = None, Mtot = None, q = None, Mc = None, mu = None, tolerance = 1e5):
    '''.
    Update the mass 1 value given to that calculated if the tolerance is not met.

    This function will check to see if the mass 1 value passed to the
    function is the same or within some tolerance to the mass 1 value
    calculated. If there is not mass 1 value passed into the function,
    or the tolerance is exceeded, then the calculated mass 1 value
    becomes the value used and returned as the mass 1.
    
    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given, default = None

        m2 = mass of second binary object, units = same as the other
             mass value given, default = None

        Mtot = total mass of the system, units = same as the other
               mass values given, default = None

        q = mass ratio of the system, units = NA, default = None

        Mc = chirp mass of the system, units = same as the other mass
             values given, default = None

        mu = reduced mass of the system, units = same as the other
             mass values given, default = None

        tolarance = what the difference has to be less than or equal
                    to in order to not replace the given value with that
                    calculated, units = NA, default = 1e5
    
    Outputs:

        m1 = mass of first binary object, units = same as the units of
             the masses passed to function

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
    if isnull(m1) or abs(m1 - m1_calced) >= tolerance:
        m1 = m1_calced

    # If none of the above criteria are met then the m1 value passed to the function
    # stays as the m1 value.
    else:
        pass
    return m1



def update_m2(m1 = None, m2 = None, Mtot = None, q = None, Mc = None, mu = None, tolerance = 1e5):
    '''.

    Update the mass 2 value given to that calculated if the tolerance
    is not met. This function will check to see if the mass 2 value
    passed to the function is the same or within some tolerance to the
    mass 2 value calculated. If there is not mass 2 value passed into
    the function, or the tolerance is exceeded, then the calculated
    mass 2 value becomes the value used and returned as the mass 2.

    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given, default = None

        m2 = mass of second binary object, units = same as the other
             mass value given, default = None

        Mtot = total mass of the system, units = same as the other
               mass values given, default = None

        q = mass ratio of the system, units = NA, default = None

        Mc = chirp mass of the system, units = same as the other mass
             values given, default = None

        mu = reduced mass of the system, units = same as the other
             mass values given, default = None

        tolarance = what the difference has to be less than or equal
                    to in order to not replace the given value with that
                    calculated, units = NA, default = 1e5
    
    Outputs:

        m2 = mass of first binary object, units = same as the units of
             the masses passed to function

    '''
    
    # Try to calculate m2 from whatever given mass values you have
    # using the find_m1_m2 function
    try:
        m2_calced = find_m1_m2(m1, m2, Mtot, q, Mc, mu)[1]
    # If the find_m1_m2 function fails, then raise an error becuase
    # none of the mass values can be calculated.
    except:
        raise ValueError("Not enough mass values available to calculate m1 and m2.")

    # If no m2 was passed to the function or the difference between
    # the value passed and the value calculated is greater than the
    # tolerance, the calculated m2 value is the the mass value used
    # for m2.
    if isnull(m2) or abs(m2 - m2_calced) >= tolerance:
        m2 = m2_calced

    # If none of the above criteria are met then the m2 value passed
    # to the function stays as the m2 value.
    else:
        pass
    return m2



###############
def update_Mc(m1, m2, Mc = None, tolerance = 1e5):
    '''.

    Update the chirp mass value given to that calculated if the
    tolerance is not met.  This function will check to see if the
    chirp mass value passed to the function is the same or within some
    tolerance to the chirp mass value calculated given the m1 and
    m2. If there is not chirp mass value passed into the function, or
    the tolerance is exceeded, then the calculated chirp mass value
    becomes the value used and returned as the chirp mass.
    
    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given

        Mc = chirp mass of the system, units = same as the other mass
             values given, default = None

        tolerance = what the difference has to be less than or equal
                    to in order to not replace the given value with that
                    calculated, units = NA, default = 1e5
    
    Outputs:

        Mc = chirp mass of the system, units = same as the units of
             the masses passed to function

    '''
    
    # Calculate the chirp mass from the given m1 and m2
    Mc_calced = Mc_calc(m1, m2)

    # If no chirp mass was passed to the function or the difference
    # between the value passed and the value calculated is greater
    # than the tolerance, the calculated chirp mass value is the the
    # mass value used for chirp mass.
    if isnull(Mc) or abs(Mc - Mc_calced) >= tolerance:
        Mc = Mc_calced

    # If none of the above criteria are met then the chirp mass value
    # passed to the function stays as the chirp mass value.
    else:
        pass
    return Mc



def update_Mtot(m1, m2, Mtot = None, tolerance = 1e5):
    '''.

    Update the total mass value given to that calculated if the
    tolerance is not met.  This function will check to see if the
    total mass value passed to the function is the same or within some
    tolerance to the total mass value calculated given the m1 and
    m2. If there is not total mass value passed into the function, or
    the tolerance is exceeded, then the calculated total mass value
    becomes the value used and returned as the total mass.

    
    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given

        Mtot = total mass of the system, units = same as the other
               mass values given, default = None

        tolarance = what the difference has to be less than or equal
                    to in order to not replace the given value with that
                    calculated, units = NA, default = 1e5
    
    Outputs:

        Mtot = total mass of the system, units = same as the units of
               the masses passed to function

    '''
    
    # Calculate the total mass from the given m1 and m2
    Mtot_calced = Mtot_calc(m1, m2)

    # If no total mass was passed to the function or the difference
    # between the value passed and the value calculated is greater
    # than the tolerance, the calculated total mass value is the the
    # mass value used for total mass.
    if isnull(Mtot) or abs(Mtot - Mtot_calced) >= tolerance:
        Mtot = Mtot_calced

    # If none of the above criteria are met then the total mass value
    # passed to the function stays as the total mass value.
    else:
        pass
    return Mtot



def update_mu(m1, m2, mu = None, tolerance = 1e5):
    '''.
    
    Update the reduced mass value given to that calculated if the
    tolerance is not met.  This function will check to see if the
    reduced mass value passed to the function is the same or within
    some tolerance to the reduced mass value calculated given the m1
    and m2. If there is not reduced mass value passed into the
    function, or the tolerance is exceeded, then the calculated
    reduced mass value becomes the value used and returned as the
    reduced mass.

    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given

        mu = reduced mass of the system, units = same as the other
             mass values given, default = None

        tolarance = what the difference has to be less than or equal
                    to in order to not replace the given value with that
                    calculated, units = NA, default = 1e5
    
    Outputs:

        mu = reduced mass of the system, units = same as the units of
             the masses passed to function

    '''
    
    # Calculate the reduced mass from the given m1 and m2
    mu_calced = mu_calc(m1, m2)

    # If no reduced mass was passed to the function or the difference
    # between the value passed and the value calculated is greater
    # than the tolerance, the calculated reduced mass value is the the
    # mass value used for reduced mass.
    if isnull(mu) or abs(mu - mu_calced) >= tolerance:
        mu = mu_calced

    # If none of the above criteria are met then the reduced mass
    # value passed to the function stays as the reduced mass value.
    else:
        pass

    return mu




def update_q(m1, m2, q = None, tolerance = 0.01):
    '''.
    
    Update the mass ratio value given to that calculated if the
    tolerance is not met.  This function will check to see if the mass
    ratio value passed to the function is the same or within some
    tolerance to the mass ratio value calculated given the m1 and
    m2. If there is not a mass ratio value passed into the function,
    or the tolerance is exceeded, then the calculated mass ratio value
    becomes the value used and returned as the mass ratio.

    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given

        q = mass ratio of the system, units = NA, default = None

        tolerance = what the difference has to be less than or equal
                    to in order to not replace the given value with that
                    calculated, units = NA, default = 0.01
    
    Outputs:

        q = mass ratio of the system, units = NA, default = None

    '''
    
    # Calculate the mass ratio from the given m1 and m2
    q_calced = q_calc(m1, m2)

    # If no mass ratio was passed to the function or the difference
    # between the value passed and the value calculated is greater
    # than the tolerance, the calculated mass ratio value is the the
    # value used for mass ratio.
    if isnull(q) or abs(q - q_calced) >= tolerance:
        q = q_calced

    # If none of the above criteria are met then the mass ratio value
    # passed to the function stays as the mass ratio value.
    else:
        pass

    return q



def update_masses(m1, m2, Mtot, Mc, mu, q):
    '''.

    Update all six of the mass values used to fully describe a binary
    system to make sure the arugments passed to it are all
    compatibable with each other according to the equations. NOTE:
    This function ONLY uses the default tolerances in all the
    individual update functions. There is no way to set user defined
    tolerances. This function complies all of the update_* functions
    into one so that the user can fully update all six mass values
    easily in one command. There is one caveat to this function, the
    tolerance used in all of the update_* functions must be the
    default tolerance.  The user cannot define the tolerances
    themselves for the individual update_* functions.


    Inputs:

        m1 = mass of first binary object, units = same as the other
             mass value given, default = None

        m2 = mass of second binary object, units = same as the other
             mass value given, default = None

        Mtot = total mass of the system, units = same as the other
               mass values given, default = None

        q = mass ratio of the system, units = NA, default = None

        Mc = chirp mass of the system, units = same as the other mass
             values given, default = None

        mu = reduced mass of the system, units = same as the other
             mass values given, default = None
    
    Outputs:

        m1 = mass of first binary object, units = same as the other
             mass value given

        m2 = mass of second binary object, units = same as the other
             mass value given

        Mtot = total mass of the system, units = same as the other
               mass values given

        q = mass ratio of the system, units = NA

        Mc = chirp mass of the system, units = same as the other mass
             values given

        mu = reduced mass of the system, units = same as the other
             mass values given

    '''
   
    # Update m1.
    m1_updated = update_m1(m1, m2, Mtot, q, Mc, mu)

    # Update m2.
    m2_updated = update_m2(m1, m2, Mtot, q, Mc, mu)

    # Update Mtot.
    Mtot_updated = update_Mtot(m1, m2, Mtot)

    # Update q.
    q_updated = update_q(m1, m2, q)

    # Update Mc.
    Mc_updated = update_Mc(m1, m2, Mc)

    # Update mu.
    mu_updated = update_mu(m1, m2, mu)

    # In order to know whether or not any of the mass values were
    # updated we need to keep track of the mass values that actually
    # are updated from the value initially given to the function.
    # This is done by appending the names of the variables that were
    # updated to an array that will be returned along with the updated
    # mass values.

    # First create the empty array.
    updated_masses = []

    # Next check if any of the mass values have been updated and if so
    # append the mass name to the array.
    if m1_updated != m1:
        updated_masses.append("m1")
    if m2_updated != m2:
        updated_masses.append("m2")
    if Mtot_updated != Mtot:
        updated_masses.append("Mtot")
    if q_updated != q:
        updated_masses.append("q")
    if Mc_updated != Mc:
        updated_masses.append("Mc")
    if mu_updated != mu:
        updated_masses.append("mu")

    # Return all the updated mass values and the array with the names
    # of the values that have been updated.
    return ([m1_updated,m2_updated,Mtot_updated,Mc_updated,mu_updated,q_updated], updated_masses)






###########################
#  STRAIN CALCULATIONS
###########################

def strain_calc(Mc,Dl,f_grav):
    '''.

    Calculate strain amplitude using the NANOGrav "standard" strain
    equation as used in e.g. 2020ApJ...900..102A (the NANOGrav GW
    search paper that targeted 3C66B), accounting for self-consistent
    use of units.

    Inputs:
        Mc = chirp mass, units = M_solar
        Dl = luminosity distance, units = Mpc
        f_grav = gravitational wave frequency, units = s^-1(Hz)

    Outputs:
        h = GW characteristic strain, units = NA

    '''

    # Define constants used in strain equation.
    G = 4.5170e-48 #gravitational constant in units of Mpc^3 M_solar^-1 s^-2   
    c = 9.7146e-15 #speed of light in units of Mpc s^-1
    
    # Check that the number of arugments given to the function is
    # correct and they are all some form of a number.
    if isinstance(Mc, (int, float)) and isinstance(Dl, (int, float)) and isinstance(f_grav, (int, float)):
        # Calculate the strain for the values given and return it. 
        # equation from https://iopscience.iop.org/article/10.3847/1538-4357/ababa1/pdf, and http://www.physics.usu.edu/Wheeler/GenRel2013/Notes/GravitationalWaves.pdf
        h = 2*(((np.pi*f_grav)**(2/3))*((G*Mc)**(5/3)))/((c**4)*(Dl))
        return h
    # If either any of the arguments are not numerical then throw an error.
    else:
        raise RuntimeError("Arguments given are incorrect. 3 numerical values needed (Mc, Dl, f_grav)")



###########################
#  FREQUENCY CONVERSION
###########################

def freq_calc(T = None, f_orb = None, f_grav = None):
    """.

    Read any of the Orbital Period in the Source Frame (in years), the
    orbital frequency in the source frame (in Hz), and the dominant
    gravitational wave frequency assuming near-circular orbits (in Hz)
    to calculate those values missing from the inputs. If the input
    values do not agree with each other it will return the newly
    calculated estimates, and reserve the old inputs to be checked
    later.

    Args: 
    T = Orbital Period in Years
    f_orb = Orbital frequency in Hertz
    f_grav = Dominant gravitational wave frequency in Hertz
    These will also be the outputs

    """
    
    if not isinstance(T, (int, float, type(None))) and not isinstance(f_orb, (int, float, type(None))) and not isinstance(f_grav, (int, float, type(None))):
        raise TypeError("Arguments must be numerical or empty.")
        
    if not isnull(T) and not isnull(f_orb) and f_grav != None:
        return [f_orb, T, f_grav]
    
    if not isnull(T):
        #change T into seconds
        T_sec = T*31536000
        if isnull(f_orb):
            f_orb = (2*np.pi)/T_sec
        if isnull(f_grav):
            f_grav = 2*f_orb
    elif not isnull(f_orb):
        #perform calculations using f_orb
        T = (2*np.pi)/f_orb #in seconds
        T = T/31536000 #in years
        if f_grav == None:
            f_grav = 2*f_orb
    elif not f_grav == None:
        #perform calculations using f_grav
        T_sec = (4*np.pi)/f_grav #in seconds
        T = T_sec/31536000 #in years
        f_orb = (0.5)*f_grav
        #should not need to check to see if new calculations are
        #needed for assignment as both T and f_orb==None to reach this
        #statement
    else:
        raise RuntimeError("Please make sure to include values for at least one of the arguments.")
    
    # Array of outputs (built with priority for T)
   
    # From here, frequency values can be reinserted into the BOBcat
    # database.
    return [f_orb, T, f_grav]



def update_Tforb(T = None, f_orb = None, f_grav = None, tolerance = 1e-5):
    
    """.

    Checks self-consistency of values T, f_orb, and f_grav provided to
    the function.

    JESSICA PLEASE ADD HERE A CLEAR DESCRIPTION OF WHAT THE FUNCTION
    DOES AND WHAT T, f_orb and f_grav ARE!!!

    """

    T_calced, f_orb_calced = freq_calc(T, f_orb, f_grav)

    # If no chirp mass was passed to the function or the difference between the value passed and
    # the value calculated is greater than the tolerance, the calculated chirp mass value is the
    # the mass value used for chirp mass.
    if T == None or abs(T - T_calced) >= tolerance:
        T = T_calced

    if f_orb == None or abs(f_orb - f_orb_calced) >= tolerance:
        f_orb = f_orb_calced

    # If none of the above criteria are met then the chirp mass value passed to the function
    # stays as the chirp mass value.
    else:
        pass
    return T, f_orb






    

###########################
#  COSMOLOGY FUNCTIONS
###########################

def cosmo_calc(z,H0=70,WM=0.3,WV=0.000085): #Inputs are: z, H0, WM, WV
    """.

    This is the BOBcat cosmological distance calculator. It was built
    upon the following: Cosmology calculator
    (www.astro.ucla.edu/~wright/CosmoCalc.html) ala Ned Wright
    (www.astro.ucla.edu/~wright) Cosmology calculator python version
    (www.astro.ucla.edu/~wright/CC.python) ala James Schombert
    (abyss.uoregon.edu/~js/)
    
    This version has been simplified to only include inputs necessary
    for the desired output array.

    Required Input values = redshift
    Additional Input values = Ho, Omega_m, Omega_vac
    
    Output values = redshift, comoving radial distance (in Mpc),
    luminosity distance (in Mpc), and the angular diameter distance
    scale (in kpc/")
    
    By default, this calculator assumes a flat universe in line with
    the benchmark model. Other universes can be built via custom
    values of WM and WV.

    """
    #We first want to assume the benchmark model when not provided
    #cosmological parameters
#    if b==None and c==None:
#        WM = 0.3                        # Omega(matter)
#        WV = 1.0 - WM - 0.4165/(H0*H0)  # Omega(vacuum) or lambda
#    elif b!=None and c==None:
#        WM = b                          # Omega(matter)
#        WV = 1.0 - WM - 0.4165/(H0*H0)  # Omega(vacuum) or lambda
#    elif b==None and c!=None:
#        WM = 1.0 - c - 0.4165/(H0*H0)   # Omega(matter)
#        WV = c                          # Omega(vacuum) or lambda
#    else:
#    H0 = a
#    WM = b                          # Omega(matter)
#    WV = c                          # Omega(vacuum) or lambda
        
    #Next, initialize constants
    
    WR = 0.        # Omega(radiation)
    WK = 0.        # Omega curvaturve = 1-Omega(total)
    c = 299792.458 # velocity of light in km/sec
    DCMR = 0.0     # comoving radial distance in units of c/H0
    DCMR_Mpc = 0.0 
    DA = 0.0       # angular size distance
    DA_Mpc = 0.0
    kpc_DA = 0.0
    DL = 0.0       # luminosity distance
    DL_Mpc = 0.0
    a = 1.0        # 1/(1+z), the scale factor of the Universe
    az = 0.5       # 1/(1+z(object))
    
    h = H0/100.
    WR = 4.165E-5/(h*h)   # includes 3 massless neutrino species, T0 = 2.72528
    WK = 1-WM-WR-WV
    az = 1.0/(1+1.0*z)

    #scale factor calculations
    n=1000         # number of points in integrals
    #Perform integral over a=1/(1+z) from az to 1 in n steps, midpoint rule
    for i in range(n):
        a = az+(1-az)*(i+0.5)/n
        adot = np.sqrt(WK+(WM/a)+(WR/(a*a))+(WV*a*a))
        #finding comoving radial distance
        DCMR = DCMR + 1./(a*adot)

    DCMR = (1.-az)*DCMR/n
    DCMR_Mpc = (c/H0)*DCMR
    
    #Calculate the tangential comoving distance
    ratio = 1.00
    x = np.sqrt(abs(WK))*DCMR
    if x > 0.1:
        if WK > 0:
            ratio =  0.5*(np.exp(x)-np.exp(-x))/x 
        else:
            ratio = np.sin(x)/x
    else:
        y = x*x
        if WK < 0: 
            y = -y
            ratio = 1. + y/6. + y*y/120.
    DCMT = ratio*DCMR

    #calculating angular diameter distances and ratios
    DA = az*DCMT
    DA_Mpc = (c/H0)*DA
    kpc_DA = DA_Mpc/206.264806

    #calculating luminosity distances
    DL = DA/(az*az)
    DL_Mpc = (c/H0)*DL


    # Returns an array of redshift, comoving radial distance (in Mpc),
    # luminosity distance (in Mpc), and the angular diameter distance
    # scale (in kpc/") From this, we can reinsert distance values into
    # the BOBcat database for use in calculating 
    return (DL_Mpc, DCMR_Mpc, kpc_DA)


