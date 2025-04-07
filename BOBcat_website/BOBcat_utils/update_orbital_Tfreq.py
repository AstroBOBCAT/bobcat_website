
from .frequency_calculator import freq_calc


def update_Tforb(T = None, f_orb = None, f_grav = None, tolerance = 1e-5):
    
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
##############