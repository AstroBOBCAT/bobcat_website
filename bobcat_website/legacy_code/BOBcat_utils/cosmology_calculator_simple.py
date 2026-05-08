#This is the BOBcat cosmological distance calculator. It is built off of Ned Wright's Cosmology Calculator.
#This version has been simplified to only include inputs necessary for the desired output array.

#import tools
import numpy as np 
from math import *

#DEFINING THE FUNCTION:
def cosmo_calc(z,a=None,b=None,c=None): #Inputs are: z, H0, WM, WV
    """
    This is the BOBcat cosmological distance calculator. It was built upon the following:
    Cosmology calculator (www.astro.ucla.edu/~wright/CosmoCalc.html) ala Ned Wright (www.astro.ucla.edu/~wright)
    Cosmology calculator python version (www.astro.ucla.edu/~wright/CC.python) ala James Schombert (abyss.uoregon.edu/~js/)
    
    Required Input values = redshift
    Additional Input values = Ho, Omega_m, Omega_vac
    
    Output values = redshift, comoving radial distance (in Mpc), luminosity distance (in Mpc), and the angular diameter distance scale (in kpc/")
    
    By default, this calculator assumes a flat universe in line with the benchmark model. Other universes can be built via custom values of WM and WV.
    """
    #We first want to assume the benchmark model when not provided cosmological parameters
    if a==None:                          
        H0 = 70                         # Hubble constant
    else:
        H0 = a                          # Hubble constant
    if b==None and c==None:
        WM = 0.3                        # Omega(matter)
        WV = 1.0 - WM - 0.4165/(H0*H0)  # Omega(vacuum) or lambda
    elif b!=None and c==None:
        WM = b                          # Omega(matter)
        WV = 1.0 - WM - 0.4165/(H0*H0)  # Omega(vacuum) or lambda
    elif b==None and c!=None:
        WM = 1.0 - c - 0.4165/(H0*H0)   # Omega(matter)
        WV = c                          # Omega(vacuum) or lambda
    else:
        WM = b                          # Omega(matter)
        WV = c                          # Omega(vacuum) or lambda
        
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
        adot = sqrt(WK+(WM/a)+(WR/(a*a))+(WV*a*a))
        #finding comoving radial distance
        DCMR = DCMR + 1./(a*adot)

    DCMR = (1.-az)*DCMR/n
    DCMR_Mpc = (c/H0)*DCMR
    
    #Calculate the tangential comoving distance
    ratio = 1.00
    x = sqrt(abs(WK))*DCMR
    if x > 0.1:
        if WK > 0:
            ratio =  0.5*(exp(x)-exp(-x))/x 
        else:
            ratio = sin(x)/x
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
    DL_Mpc = (c/H0)*DL# * 1000000


    #Returns an array of redshift, comoving radial distance (in Mpc), luminosity distance (in Mpc), and the angular diameter distance scale (in kpc/")
    return DL_Mpc, DCMR_Mpc, kpc_DA

#from this, we can reinsert distance values into the BOBcat database for use in calculating strain
