import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..")) # this seems to be the only one that actually works


import pytest
from BOBcat_utils import *


def test_NED_name_resolver():
    name = "3C66B"
    NED_name = NED_name_resolver(name)
    assert NED_name == "UGC 01841"

def test_NED_name_resolver_notstr():
    name = 3667
    with pytest.raises(TypeError) as excinfo:
        NED_name_resolver(name)
    assert str(excinfo.value) == "Name must be a string."

def test_NED_name_resolver_notindb():
    name = "Sam"
    with pytest.raises(SystemError) as excinfo:
        NED_name_resolver(name)
    assert str(excinfo.value) == "Name given is not in NED database."

def test_strain_calc():
    strain = strain_calc(7.9e8, 85, 60.4e-9)
    assert strain == 7.269388639002558e-15

def test_strain_calc_badparams():
    with pytest.raises(RuntimeError) as excinfo:
        strain_calc("a", "b", 5)
    assert str(excinfo.value) == "Arguments given are incorrect. 3 numerical values needed (Mc, Dl, f_grav)"

def test_coord_finder():
    name = "oj287"
    coords = coord_finder(name)
    assert coords == ('08h54m48.875s', '+20d06m30.6396s')

def test_coord_finder_notstr():
    name = 34.3
    with pytest.raises(TypeError) as excinfo:
        coord_finder(name)
    assert str(excinfo.value) == "Name must be a string."

def test_coord_finder_notinastropy():
    name = "sam"
    with pytest.raises(SystemError) as excinfo:
        coord_finder(name)
    assert str(excinfo.value) == "Name of source is in shorthand or not in an established database."

def test_NED_z():
    ra = 133.7036
    dec = 20.1085
    z = NED_z(ra, dec)
    assert z == 0.3056

def test_NED_z_tol():
    ra = 133.7036
    dec = 20.1085
    tol = 0.001
    z = NED_z(ra, dec, tol)
    assert z == 0.3056

def test_NED_z_badparams():
    ra = "02h23m11.4112s"
    dec = "+42d59m31.3853s"
    with pytest.raises(RuntimeError) as excinfo:
        NED_z(ra, dec)
    assert str(excinfo.value) == "Arguments given are incorrect. Make sure ra and dec are in degrees."

def test_NED_name():
    ra = 133.7036
    dec = 20.1085
    name = NED_name(ra, dec)
    assert name == "OJ +287"

def test_NED_name_tol():
    ra = 133.7036
    dec = 20.1085
    tol = 0.001
    name = NED_name(ra, dec, tol)
    assert name == "OJ +287"

def test_NED_name_badparams():
    ra = "02h23m11.4112s"
    dec = "+42d59m31.3853s"
    with pytest.raises(RuntimeError) as excinfo:
        NED_name(ra, dec)
    assert str(excinfo.value) == "Arguments given are incorrect. Make sure ra and dec are in degrees."

def test_coord_converter():
    ra = "02h23m11.4112s"
    dec = "+42d59m31.3853s"
    ra_deg, dec_deg = coord_converter(ra, dec)
    assert ra_deg, dec_deg == (35.79754666666666, 42.99205147222222)

def test_coord_converter_badparams():
    ra = "02h23m11.4112s"
    dec = "1259m31.3853s"
    with pytest.raises(SystemError) as excinfo:
        coord_converter(ra, dec)
    assert str(excinfo.value) == "Make sure ra and dec are entered correctly."

def test_coord_converter_notstr():
    ra = "02h23m11.4112s"
    dec = 20.1085
    with pytest.raises(TypeError) as excinfo:
        coord_converter(ra, dec)
    assert str(excinfo.value) == "ra and dec must be strings."

def test_mu_calc():
    m1 = 5
    m2 = 8
    mu = mu_calc(m1, m2)
    assert mu == 3.076923076923077

def test_Mc_calc():
    m1 = 1
    m2 = 2
    Mc = Mc_calc(m1, m2)
    assert Mc == 1.2167286837864115

def test_q_calc1():
    m1 = 4
    m2 = 3
    q = q_calc(m1, m2)
    assert q == 0.75

def test_q_calc2():
    m1 = 3
    m2 = 4
    q = q_calc(m1, m2)
    assert q == 0.75 

def test_Mtot_calc():
    m1 = 10
    m2 = 8
    Mtot = Mtot_calc(m1, m2)
    assert Mtot == 18

def test_update_Mtot():
    m1 = 3
    m2 = 1
    Mtot_given = 4
    Mtot = update_Mtot(m1, m2, Mtot_given)
    assert Mtot == 4

def test_update_Mtot_badgiven():
    m1 = 3e8
    m2 = 1e8
    Mtot_given = 8e8
    Mtot = update_Mtot(m1, m2, Mtot_given)
    assert Mtot == 4e8

def test_update_Mtot_tol():
    m1 = 3
    m2 = 1
    Mtot_given = 4
    tol = 0.1
    Mtot = update_Mtot(m1, m2, Mtot_given, tol)
    assert Mtot == 4

def test_update_Mc():
    m1 = 3
    m2 = 1
    Mc_given = 1.4650780257917608
    Mc = update_Mc(m1, m2, Mc_given)
    assert Mc == 1.4650780257917608

def test_update_Mc_badgiven():
    m1 = 3e7
    m2 = 1e7
    Mc_given = 1.5e7
    Mc = update_Mc(m1, m2, Mc_given)
    assert Mc == 14650780.257917622

def test_update_Mc_tol():
    m1 = 3
    m2 = 1
    Mc_given = 1.5
    tol = 0.1
    Mc = update_Mc(m1, m2, Mc_given, tol)
    assert Mc == 1.5

def test_update_mu():
    m1 = 3
    m2 = 1
    mu = update_mu(m1, m2)
    assert mu == 0.75

def test_update_mu_badgiven():
    m1 = 3e6
    m2 = 1e6
    mu_given = 7e6
    mu = update_mu(m1, m2, mu_given)
    assert mu == 7.5e5

def test_update_mu_tol():
    m1 = 3
    m2 = 1
    mu_given = 0.8
    tol = 0.5
    mu = update_mu(m1, m2, mu_given, tol)
    assert mu == 0.8

def test_update_q():
    m1 = 3e10
    m2 = 4e10
    q = update_q(m1, m2)
    assert q == 0.75

def test_update_q_badgiven():
    m1 = 4
    m2 = 3
    q_given = 7
    q = update_q(m1, m2, q_given)
    assert q == 0.75

def test_update_q_tol():
    m1 = 4e-2
    m2 = 3e-2
    q_given = 0.8
    tol = 0.6
    q = update_q(m1, m2, q_given, tol)
    assert q == 0.8









