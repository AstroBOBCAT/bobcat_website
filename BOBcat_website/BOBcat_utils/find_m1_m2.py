## find_m1_m2.py holds the code for the find_m1_m2() function. This function takes in all
## six mass values used to describe a binary system. From any two out of the six values,
## m1 and m2 can be found. We prioritize m1 and m2 values because calculating any of the 
## other four mass values is easiest from m1 and m2. Therefore, this function will determine
## which two (minimum) mass values were passed to it and then calculate m1 and m2 from there.
## The elif statements are put in an order such that the easiest calculations are put at the
## beginning and should complete first. This means if more than two mass values are passed to 
## the function, the simplest calculations will occur to find m1 and m2 values.




##################
def find_m1_m2(m1 = None, m2 = None, Mtot = None, q = None, Mc = None, mu = None):
    '''
    Find the values of m1 and m2 for a binary system given at least two of the six common
    mass parameters, i.e. a minimum of two values from m1, m2, Mtot, q, Mc, and mu are 
    needed to calculate m1 and m2.

    Inputs:
        m1 = mass of first binary object, units = same as the other mass value given, default = None
        m2 = mass of second binary object, units = same as the other mass value given, default = None
        Mtot = total mass of the system, units = same as the other mass values given, default = None
        q = mass ratio of the system, units = NA, default = None
        Mc = chirp mass of the system, units = same as the other mass values given, default = None
        mu = reduced mass of the system, units = same as the other mass values given, default = None
    
    Outputs:
        m1 = mass of first binary object, units = same as the units of the masses passed to function
        m2 = mass of second binary object, units = same as the units of the masses passed to function
    '''
    
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
    return(m1,m2)
 #####################