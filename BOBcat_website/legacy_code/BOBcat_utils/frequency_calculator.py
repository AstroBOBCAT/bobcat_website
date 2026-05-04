#This is the BOBcat SMBHB frequency calculator. It calculates orbital period, orbital frequency, and the dominant gravitational wave frequency (2*orbital frequency). This gravitational wave frequency is dominant in circular binaries. Work is currently continuing toward adding and accounting for eccentricity.

#import needed tools
import numpy as np


#FREQUENCY FUNCTION
#create the function to read and calculate orbital period and orbital frequency values.
def freq_calc(T = None, f_orb = None, f_grav = None):
    """
    This is the BOBcat frequency calculator (in Hz). It reads the Orbital Period in the Source Frame (in years),
    the orbital frequency in the source frame (in Hz), and the dominant gravitational wave frequency assuming near-
    circular orbits (in Hz) to calculate those values missing from the inputs. If the inputted values do not agree 
    with each other it will return the newly calculated estimates, and reserve the old inputs to be checked later.

    Args: 
    T = Orbital Period in Years
    f_orb = Orbital frequency in Hertz
    f_grav = Dominant gravitational wave frequency in Hertz
    These will also be the outputs
    """

    
    if not isinstance(T, (int, float, type(None))) and not isinstance(f_orb, (int, float, type(None))) and not isinstance(f_grav, (int, float, type(None))):
        raise TypeError("Arguments must be numerical or empty.")





        
    if T!=None:
        #change T into seconds
        T_sec = T*31536000
        if f_orb == None:
            f_orb = (2*np.pi)/T_sec
        if f_grav == None:
            f_grav = 2*f_orb
    elif f_orb!=None:
        #perform calculations using f_orb
        T = (2*np.pi)/f_orb #in seconds
        T = T/31536000 #in years
        if f_grav == None:
            f_grav = 2*f_orb
    elif f_grav!=None:
        #perform calculations using f_grav
        T_sec = (4*np.pi)/f_grav #in seconds
        T = T_sec/31536000 #in years
        f_orb = (0.5)*f_grav
        #should not need to check to see if new calculations are needed for assignment as both T and f_orb==None to reach this statement
    else:
        raise RuntimeError("Please make sure to include values for at least one of the arguments.")
    
    #array of outputs (built with priority for T)
   
    return T, f_orb, f_grav

#from here, frequency values can be reinserted into the BOBcat database.
