## update_all_masses.py has the code for the function update_masses(). This function
## complies all of the update_* functions into one so that the user can fully update
## all six mass values easily in one command. There is one caveat to this function,
## the tolerance used in all of the update_* functions must be the default tolerance.
## The user cannot define the tolerances themselves for the individual update_* functions.


######
# Import the need libraries and modules for the function to work.
from .update_m1 import update_m1
from .update_m2 import update_m2
from .update_Mc import update_Mc
from .update_Mtot import update_Mtot
from .update_mu import update_mu
from .update_q import update_q
######


################
def update_masses(m1 = None, m2 = None , Mtot = None, q = None, Mc = None, mu = None):
    '''
    Update all six of the mass values used to fully describe a binary system to make sure the arugments
    passed to it are all compatibable with each other according to the equations. NOTE: This function 
    ONLY uses the default tolerances in all the individual update functions. There is no way to set
    user defined tolerances.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given, default = None
        m2 = mass of second binary object, units = same as the other mass value given, default = None
        Mtot = total mass of the system, units = same as the other mass values given, default = None
        q = mass ratio of the system, units = NA, default = None
        Mc = chirp mass of the system, units = same as the other mass values given, default = None
        mu = reduced mass of the system, units = same as the other mass values given, default = None
    
    Outputs:
        m1 = mass of first binary object, units = same as the other mass value given
        m2 = mass of second binary object, units = same as the other mass value given
        Mtot = total mass of the system, units = same as the other mass values given
        q = mass ratio of the system, units = NA
        Mc = chirp mass of the system, units = same as the other mass values given
        mu = reduced mass of the system, units = same as the other mass values given
    
    '''
    m1_input = m1
    m2_input = m2
    Mtot_input = Mtot
    q_input = q
    Mc_input = Mc
    mu_input = mu
   
    # Update m1.
    m1 = update_m1(m1, m2, Mtot, q, Mc, mu)

    # Update m2.
    m2 = update_m2(m1, m2, Mtot, q, Mc, mu)

    # Update Mtot.
    Mtot = update_Mtot(m1, m2, Mtot)

    # Update q.
    q = update_q(m1, m2, q)

    # Update Mc.
    Mc = update_Mc(m1, m2, Mc)

    # Update mu.
    mu = update_mu(m1, m2, mu)

    # In order to know whether or not any of the mass values were updated we need to keep track
    # of the mass values that actually are updated from the value initially given to the function.
    # This is done by appending the names of the variables that were updated to an array that
    # will be returned along with the updated mass values.

    # First create the empty array.
    updated_masses = []

    # Next check if any of the mass values have been updated and if so append the mass name to the 
    # array.
    if m1_input != m1:
        updated_masses.append("m1")
    if m2_input != m2:
        updated_masses.append("m2")
    if Mtot_input != Mtot:
        updated_masses.append("Mtot")
    if q_input != q:
        updated_masses.append("q")
    if Mc_input != Mc:
        updated_masses.append("Mc")
    if mu_input != mu:
        updated_masses.append("mu")

    # Return all the updated mass values and the array with the names of the values that have been updated.
    return ([(m1, m2, Mtot, q, Mc, mu), updated_masses])
################
  