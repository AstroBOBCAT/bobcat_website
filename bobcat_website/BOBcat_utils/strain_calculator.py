## strain_calculator.py contains the code for the function strain_calc(). This function will calculate the 
## gravitational wave (GW) characteristic strain, h. The equation used are those associated as the 
## NANOGrav standard strain equation. 


######
# Import the need libraries and modules for the function to work.
import numpy as np
######


#################
def strain_calc(Mc,Dl,f_grav):
    '''
    Calculate strain amplitude using the NANOGrav standard strain equation. 

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
    
    # Check that the number of arugments given to the function is correct and they are all some form of a number.          
    if isinstance(Mc, (int, float)) and isinstance(Dl, (int, float)) and isinstance(f_grav, (int, float)):
        # Calculate the strain for the values given and return it. 
        # equation from https://iopscience.iop.org/article/10.3847/1538-4357/ababa1/pdf, and http://www.physics.usu.edu/Wheeler/GenRel2013/Notes/GravitationalWaves.pdf
        h = 2*(((np.pi*f_grav)**(2/3))*((G*Mc)**(5/3)))/((c**4)*(Dl))
        return h
    # If either any of the arguments are not numerical then throw an error.
    else:
        raise RuntimeError("Arguments given are incorrect. 3 numerical values needed (Mc, Dl, f_grav)")
##################
