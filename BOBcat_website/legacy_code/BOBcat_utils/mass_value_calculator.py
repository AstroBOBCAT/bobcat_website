
from .find_m1_m2 import find_m1_m2
from .update_all_masses import update_masses
from .Mc_calculator import Mc_calc
from .Mtot_calculator import Mtot_calc
from .mu_calculator import mu_calc
from .q_calculator import q_calc



#This is the BOBcat SMBHB Candidate Mass Value Calculator. It will read provided inputs of mass quantities and can calculate unknown mass quantities.
#Currently, the BOBcat Mass Value Calculator is equipped to calculate Mass 1, Mass 2, Total Mass, Mass Ratio, Chirp Mass, and Reduced Mass.


#THE MASS CALCULATING FUNCTION:
#As of right now, this calculator only fills in empty values, and cannot be a judge of erroneous/incongruent inputs.
#If the inputs were found via different methods/models, try entering only the inputs that used a consistent model.
def mass_val_calc(m1 = None, m2 = None, Mtot = None, q = None, Mc = None, mu = None): #creating the function, reading the collection of inputs
    """
    This is the BOBcat SMBHB mass value calculator! It will calculate estimates of Mass 1, Mass 2, Total Mass, Mass Ratio,
    Chirp Mass, and Reduced Mass (in solar masses) given known mass parameters of the binary candidate (in solar masses). 
    To successfully calculate the unknown values, at least two known parameters are needed as inputs.

    Args: (all in solar masses)
    m1 = Larger Mass
    
    m2 = Smaller Mass
    Mtot = Total Mass
    q = Mass Ratio
    Mc = Chirp Mass
    mu = Reduced Mass
    These are also the outputs
    """
    #m1_new, m2_new = find_m1_m2(m1, m2, Mtot, q, Mc, mu)
    
    
    #Here, we calculate all other values using m1 and m2

    #Mtot_new = Mtot_calc(m1,m2) #solving for Total Mass using Mass 1 and Mass 2
   #q_new = q_calc(m1,m2) #solving for Mass Ratio using Mass 1 and Mass 2
    #Mc_new = Mc_calc(m1,m2) #solving for Chirp Mass using Mass 1 and Mass 2
    #mu_new = mu_calc(m1,m2) #solving for Reduced Mass using Mass 1 and Mass 2
        
    #mass_array, updated_masses = update_masses(m1, m2, Mtot, q, Mc, mu)
    
    none_counter = 0


    if m1 == None:
        none_counter+=1
    if m2 == None:
        none_counter+=1
    if Mtot == None:
        none_counter+=1
    if q == None:
        none_counter+=1
    if Mc == None:
        none_counter+=1
    if mu == None:
        none_counter+=1


    mass_array, updated_masses = update_masses(m1, m2, Mtot, q, Mc, mu)

    if none_counter != len(updated_masses):
        raise RuntimeError("Something is wrong. Please check that you entered the correct numbers for each argument.")
    else:
        return mass_array 



    
 
























# #This is the BOBcat SMBHB Candidate Mass Value Calculator. It will read provided inputs of mass quantities and can calculate unknown mass quantities.
# #Currently, the BOBcat Mass Value Calculator is equipped to calculate Mass 1, Mass 2, Total Mass, Mass Ratio, Chirp Mass, and Reduced Mass.


# #THE MASS CALCULATING FUNCTION:
# #As of right now, this calculator only fills in empty values, and cannot be a judge of erroneous/incongruent inputs.
# #If the inputs were found via different methods/models, try entering only the inputs that used a consistent model.
# def mass_val_calc(m1,m2,Mtot,q,Mc,mu): #creating the function, reading the collection of inputs
#     """
#     This is the BOBcat SMBHB mass value calculator! It will calculate estimates of Mass 1, Mass 2, Total Mass, Mass Ratio,
#     Chirp Mass, and Reduced Mass (in solar masses) given known mass parameters of the binary candidate (in solar masses). 
#     To successfully calculate the unknown values, at least two known parameters are needed as inputs.

#     Args: (all in solar masses)
#     m1 = Larger Mass
#     # m2 = Smaller Mas
#     Mtot = Total Mass
#     q = Mass Ratio
#     Mc = Chirp Mass 
#     mu = Reduced Mass
#     These are also the outputs
#     """
#     #Setting all strings (strings replacing NaNs) to None
#     if type(m1)!=int and type(m1)!=float:
#         m1 = None
#     if type(m2)!=int and type(m2)!=float:
#         m2 = None
#     if type(Mtot)!=int and type(Mtot)!=float:
#         Mtot = None
#     if type(q)!=int and type(q)!=float:
#         q = None
#     if type(Mc)!=int and type(Mc)!=float:
#         Mc = None
#     if type(mu)!=int and type(mu)!=float:
#         mu = None
    
#     #Beginning calculations of m1 and m2:
#     if m1!=None and m2!=None: #m1 and m2 are our priority variables. These if/elif statements are used to find which parameters we are given. From there, we calculate m1, m2, or both.
#         pass #when given m1 and m2, we can jump straight to the calculation formulas.

#     #Below, the function will be choosing variables in a priority order, as in it will calculate any missing values using the first pair of inputs it detects
#     #given our series of elif statements. This priority order is guided by which parameters we believe to be most commonly reported and most easily measurable.
#     #The order is: mass 1, mass 2, total mass, mass ratio, chirp mass, and then reduced mass
    
#     elif m1!=None and Mtot!=None:
#         m2 = Mtot-m1
#     elif m2!=None and Mtot!=None:
#         m1 = Mtot-m2
#     elif m1!=None and q!=None:
#         m2 = q*m1
#     elif m2!=None and q!=None:
#         m1 = m2/q
#     elif m1!=None and Mc!=None:
#         m2 = (((2/3)**(1/3))*(Mc**5))/(((9*(Mc**5)*(m1**7))+(3*((27*(Mc**10)*(m1**14))-(4*(Mc**15)*(m1**9))))**(1/2))**(1/3)) + (((9*(Mc**5)*(m1**7))+(3*((27*(Mc**10)*(m1**14))-(4*(Mc**15)*(m1**9))))**(1/2))**(1/3))/(((18)**(1/3))*(m1**3))
#         m2 = round(m2.real, 16) #the above equation involves several radicals, so as values of Mc get further from the actual (given m1), there will be an increasingly larger complex portion. However, this portion is typically small, and so this ".real" simply deletes the complex part so calculations can continue as normal.
#     elif m2!=None and Mc!=None:
#         m1 = (((2/3)**(1/3))*(Mc**5))/(((9*(Mc**5)*(m2**7))+(3*((27*(Mc**10)*(m2**14))-(4*(Mc**15)*(m2**9))))**(1/2))**(1/3)) + (((9*(Mc**5)*(m2**7))+(3*((27*(Mc**10)*(m2**14))-(4*(Mc**15)*(m2**9))))**(1/2))**(1/3))/(((18)**(1/3))*(m2**3))
#         m1 = round(m1.real, 16)
#     elif m1!=None and mu!=None:
#         m2 = (mu*m1)/(m1-mu)
#     elif m2!=None and mu!=None:
#         m1 = (mu*m2)/(m2-mu)
#     elif Mtot!=None and q!=None:
#         m1 = Mtot/(q+1)
#         m2 = (q*Mtot)/(q+1)
#     elif Mtot!=None and Mc!=None and Mc<=(0.43527528165*Mtot): #this additional limit will prevent the calculator from outputting complex numbers by ensuring the chirp mass is in agreement with the total mass first. If they do not agree, the calculator will cut to "else"
#         m1 = (1/2)*(Mtot + (Mtot**2 - 4*(Mtot*(Mc**5))**(1/3))**(1/2))
#         m2 = (1/2)*(Mtot - (Mtot**2 - 4*(Mtot*(Mc**5))**(1/3))**(1/2))
#     elif Mtot!=None and mu!=None:
#         m1 = (1/2)*(Mtot + (Mtot**2 - 4*(Mtot*mu))**(1/2))
#         m2 = (1/2)*(Mtot - (Mtot**2 - 4*(Mtot*mu))**(1/2))
#     elif q!=None and Mc!=None:
#         m1 = Mc*((q+1)/q**3)**(1/5)
#         m2 = Mc*((q+1)*q**2)**(1/5)
#     elif q!=None and mu!=None:
#         m1 = mu*(q+1)/q 
#         m2 = mu*(q+1)
#     elif Mc!=None and mu!=None:
#         m1 = mu*(1 + ((Mc**(5/2)-mu**(3/2))/(mu**(3/2))))
#         m2 = mu*(1 + (mu**(3/2)/(Mc**(5/2)-mu**(3/2))))
#     else:
#         print('No Calculations Possible') #if we are given only one input or no inputs, the function will tell the user nothing could be calculated
#         if Mc!=None and Mtot!=None and Mc>=(0.43527528165*Mtot):
#             print('Chirp Mass too large') #flagging an error message if chirp mass is out of bounds relative to total mass and no calculations are possible because of it
#         array = np.array([m1, m2, Mtot, q, Mc, mu]) #compiles unchanged inputs into an array
#         return array #ends function here should there not be a sufficient number of inputs

#     if m2 > m1: #here, we want to ensure q remains between 0 and 1, so we need m1 to be larger than m2. If m2 is found to be larger than m1, we switch them before calculating.
#         m1_new = m2 #assigning old values to new variables
#         m2_new = m1
#         m1 = m1_new #reinserting new variables so they satisfy m1>m2 before performing calculations
#         m2 = m2_new
#     else: #if m1>m2, then nothing needs to be switched around
#         pass
    
#     #Here, we calculate all other values using m1 and m2
#     Mtot_new = m1+m2 #solving for Total Mass using Mass 1 and Mass 2
#     q_new = m2/m1 #solving for Mass Ratio using Mass 1 and Mass 2
#     Mc_new = (((m1*m2)**3)/(m1+m2))**(1/5) #solving for Chirp Mass using Mass 1 and Mass 2
#     mu_new = (m1*m2)/(m1+m2) #solving for Reduced Mass using Mass 1 and Mass 2
        
#     #with m1 and m2 known, here we check which inputs were blank, and fill them in with their corresponding values
#     #if they are known, we cross-compare inputs versus calculated values and only maintain inputs within reason (margin)
#         #- All those outside the margin are to be flagged for checking, or reassigned to a new model
#         #- As desired, change the multiplier in the nested if statement to the appropriate error bounds (default is 10%)
#     if Mtot==None:
#         Mtot = Mtot_new #assigning a calculated value if there is none inputted
#     else:
#         if abs(Mtot-Mtot_new)<=(0.1*Mtot_new):
#             Mtot = Mtot #maintaining inputted value
#         else:
#             Mtot_old = Mtot #reassign inputted (out of range) value to "old"
#             Mtot = Mtot_new #assign new calculation to output
#     if q==None:
#         q = q_new
#     else:
#         if q>1:
#             q_old = q
#             q = q_new #q_new will always be less than 1 because of the statements reassigning the larger mass to m1 for calculations
#         if abs(q-q_new)<=(0.1*q_new):
#             q = q #maintaining inputted value
#         else:
#             q_old = q #reassign old (out of range) value to "old"
#             q = q_new #assign new calculation to output
#     if Mc==None:
#         Mc = Mc_new
#     else:
#         if abs(Mc-Mc_new)<=(0.1*Mc_new):
#             Mc = Mc #maintaining inputted value
#         else:
#             Mc_old = Mc #reassign old (out of range) value to "old"
#             Mc = Mc_new #assign new calculation to output
#     if mu==None:
#         mu = mu_new
#     else:
#         if abs(mu-mu_new)<=(0.1*mu_new):
#             mu = mu #maintaining inputted value
#         else:
#             mu_old = mu #reassign old (out of range) value to "old"
#             mu = mu_new #assign new calculation to output    

#     mass_array = np.array([m1, m2, Mtot, q, Mc, mu]) #compiles unchanged inputs and newly calculated outputs into an array
#     return mass_array #returns the updated array with newly calculated values in place

# #With this array, the new values are available to be reinserted into the BOBcat database.
