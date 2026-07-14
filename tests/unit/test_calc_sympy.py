"""
Tests for BOBcat_utils/calc_sympy.py, the sympy-based drop-in alternate
to calc.py.

Numeric expectations are identical to test_calc.py: the module keeps
calc.py's conventions (mass parameters other than q are log10 solar
masses; find_m1_m2 returns log10 masses). What differs is error
handling: calc_sympy raises CalcError subclasses with descriptive
messages instead of bare RuntimeError/TypeError (the subclasses still
inherit from RuntimeError/TypeError, so old except clauses keep
working -- that inheritance is asserted below).
"""
import pytest

from BOBcat_utils import calc_sympy as calc

# Maps calc.py's short mass-parameter names (used as calc._PAIR_PRECEDENCE
# keys) to calc_sympy's descriptive keyword-argument names.
_SHORT_TO_PARAM = {
    "m1": "primary_mass_log10",
    "m2": "secondary_mass_log10",
    "Mtot": "total_mass_log10",
    "q": "mass_ratio",
    "Mc": "chirp_mass_log10",
    "mu": "reduced_mass_log10",
}


# ── Mc_calc / Mtot_calc / mu_calc / q_calc ──────────────────────────────────

def test_mc_calc_known_value():
    # log10(m1)=1 (10 Msun), log10(m2)=0 (1 Msun)
    assert calc.Mc_calc(1.0, 0.0) == pytest.approx(0.39172146296835497)


def test_mtot_calc_known_value():
    assert calc.Mtot_calc(1.0, 0.0) == pytest.approx(1.041392685158225)


def test_mu_calc_known_value():
    assert calc.mu_calc(1.0, 0.0) == pytest.approx(-0.04139268515822506)


def test_q_calc_known_value():
    assert calc.q_calc(1.0, 0.0) == pytest.approx(0.1)


def test_q_calc_symmetric_regardless_of_argument_order():
    assert calc.q_calc(1.0, 0.0) == pytest.approx(calc.q_calc(0.0, 1.0))


# ── find_m1_m2 ───────────────────────────────────────────────────────────────

def test_find_m1_m2_from_m1_and_m2_returns_log_masses():
    m1, m2 = calc.find_m1_m2(primary_mass_log10=1.0, secondary_mass_log10=0.0)
    assert m1 == pytest.approx(1.0)
    assert m2 == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("pair", calc._PAIR_PRECEDENCE)
def test_find_m1_m2_recovers_masses_from_every_parameter_pair(pair):
    # Build all six consistent parameters for m1=10^8.5, m2=10^8 Msun,
    # then check each documented input pair reproduces the masses.
    lm1, lm2 = 8.5, 8.0
    params = {
        "m1": lm1,
        "m2": lm2,
        "Mtot": calc.Mtot_calc(lm1, lm2),
        "q": calc.q_calc(lm1, lm2),
        "Mc": calc.Mc_calc(lm1, lm2),
        "mu": calc.mu_calc(lm1, lm2),
    }
    kwargs = {_SHORT_TO_PARAM[name]: params[name] for name in pair}
    m1, m2 = calc.find_m1_m2(**kwargs)
    assert m1 == pytest.approx(lm1, rel=1e-6)
    assert m2 == pytest.approx(lm2, rel=1e-6)


def test_find_m1_m2_insufficient_params_raises_with_named_params():
    with pytest.raises(calc.InsufficientParametersError) as excinfo:
        calc.find_m1_m2(primary_mass_log10=1.0)
    message = str(excinfo.value)
    assert "at least two" in message
    assert "got m1" in message


def test_find_m1_m2_mc_too_large_for_mtot_explains_the_limit():
    with pytest.raises(calc.InconsistentParametersError) as excinfo:
        calc.find_m1_m2(chirp_mass_log10=2.0, total_mass_log10=1.0)
    assert "0.43528" in str(excinfo.value)


def test_find_m1_m2_mu_too_large_for_mtot_explains_the_limit():
    with pytest.raises(calc.InconsistentParametersError) as excinfo:
        calc.find_m1_m2(total_mass_log10=8.0, reduced_mass_log10=7.9)
    assert "Mtot/4" in str(excinfo.value)


def test_find_m1_m2_non_numeric_input_names_the_argument():
    with pytest.raises(calc.InvalidParameterError) as excinfo:
        calc.find_m1_m2(primary_mass_log10="a", secondary_mass_log10=1.0)
    assert "m1" in str(excinfo.value)


def test_find_m1_m2_negative_q_rejected():
    with pytest.raises(calc.InvalidParameterError) as excinfo:
        calc.find_m1_m2(mass_ratio=-0.3, reduced_mass_log10=8.0)
    assert "positive" in str(excinfo.value)


def test_errors_remain_catchable_as_builtin_types():
    # Drop-in guarantee: code written against calc.py's bare
    # RuntimeError/TypeError still catches calc_sympy's errors.
    assert issubclass(calc.InsufficientParametersError, RuntimeError)
    assert issubclass(calc.InconsistentParametersError, RuntimeError)
    assert issubclass(calc.InvalidParameterError, TypeError)


# ── q_limit ──────────────────────────────────────────────────────────────────

def test_q_limit_roots_are_reciprocal_and_physical():
    q, multiplier = calc.q_limit(8.0, 9.0)
    assert 0 < q <= 1
    assert multiplier == pytest.approx(1 / q)


def test_q_limit_mc_too_large_raises_instead_of_exiting():
    with pytest.raises(calc.InconsistentParametersError) as excinfo:
        calc.q_limit(2.0, 1.0)
    assert "q > 1" in str(excinfo.value)


# ── update_Mc / update_Mtot / update_mu / update_q ──────────────────────────

def test_update_mc_within_tolerance_keeps_given():
    given = 0.39172146296835497
    assert calc.update_Mc(1.0, 0.0, chirp_mass_log10=given) == pytest.approx(given)


def test_update_mc_none_given_uses_calculated():
    assert calc.update_Mc(1.0, 0.0, chirp_mass_log10=None) == pytest.approx(
        calc.Mc_calc(1.0, 0.0)
    )


def test_update_mc_outside_tolerance_recomputes():
    result = calc.update_Mc(1.0, 0.0, chirp_mass_log10=1e6)
    assert result == pytest.approx(calc.Mc_calc(1.0, 0.0))


def test_update_q_within_tolerance_keeps_given():
    assert calc.update_q(1.0, 0.0, mass_ratio=0.1) == pytest.approx(0.1)


def test_update_q_outside_tolerance_recomputes():
    assert calc.update_q(1.0, 0.0, mass_ratio=0.5) == pytest.approx(0.1)


# ── strain_calc ──────────────────────────────────────────────────────────────

def test_strain_calc_known_value():
    # Mc is given as log10(Msun): log10(7.9e8) = 8.8976270912904414
    strain = calc.strain_calc(8.8976270912904414, 85, 60.4e-9)
    assert strain == pytest.approx(7.269388639002558e-15)


def test_strain_calc_bad_params_names_first_bad_argument():
    with pytest.raises(calc.InvalidParameterError) as excinfo:
        calc.strain_calc("a", "b", 5)
    assert "Mc" in str(excinfo.value)


def test_strain_calc_negative_distance_rejected():
    with pytest.raises(calc.InvalidParameterError) as excinfo:
        calc.strain_calc(8.9, -5, 1e-8)
    assert "Dl" in str(excinfo.value)


# ── tgw_calc / Kepler's laws ─────────────────────────────────────────────────

def test_tgw_calc_matches_calc_py():
    from BOBcat_utils import calc as calc_py
    assert calc.tgw_calc(0.01, 8.5, 7.9) == pytest.approx(
        calc_py.tgw_calc(0.01, 8.5, 7.9)
    )


def test_kepler_semimajor_matches_calc_py():
    from BOBcat_utils import calc as calc_py
    assert calc.kepler_semimajor(2.0, 8.5) == pytest.approx(
        calc_py.kepler_semimajor(2.0, 8.5)
    )


def test_kepler_roundtrip():
    a_pc = calc.kepler_semimajor(2.0, 8.5)
    assert calc.kepler_period(a_pc, 8.5) == pytest.approx(2.0)


def test_tgw_calc_negative_semimajor_rejected():
    with pytest.raises(calc.InvalidParameterError):
        calc.tgw_calc(-0.01, 8.5, 7.9)


# ── freq_calc / update_Tforb ─────────────────────────────────────────────────

def test_freq_calc_period_only():
    # f_orb = 1/T (no 2*pi factor), IAU year = 31557600 s
    f_orb, T, f_grav = calc.freq_calc(orbital_period_years=1.0)
    assert T == pytest.approx(1.0)
    assert f_orb == pytest.approx(1.0 / 31557600)
    assert f_grav == pytest.approx(2 * f_orb)


def test_freq_calc_forb_only():
    f_orb, T, f_grav = calc.freq_calc(orbital_frequency_hz=1e-8)
    assert f_orb == pytest.approx(1e-8)
    assert T == pytest.approx(1e8 / 31557600)
    assert f_grav == pytest.approx(2e-8)


def test_freq_calc_fgrav_only():
    f_orb, T, f_grav = calc.freq_calc(gw_frequency_hz=2e-8)
    assert f_grav == pytest.approx(2e-8)
    assert f_orb == pytest.approx(1e-8)
    assert T == pytest.approx(1e8 / 31557600)


def test_freq_calc_all_given_returned_unchanged():
    f_orb, T, f_grav = calc.freq_calc(
        orbital_period_years=1.0, orbital_frequency_hz=2e-7, gw_frequency_hz=3e-7
    )
    assert (f_orb, T, f_grav) == (2e-7, 1.0, 3e-7)


def test_freq_calc_nothing_given_raises():
    with pytest.raises(calc.InsufficientParametersError):
        calc.freq_calc()


def test_freq_calc_wrong_type_names_the_argument():
    with pytest.raises(calc.InvalidParameterError) as excinfo:
        calc.freq_calc(orbital_period_years="a")
    assert "T" in str(excinfo.value)


def test_update_tforb_fills_missing_values():
    # calc.py's update_Tforb unpacks two values from freq_calc's
    # three-element return and always crashes; the sympy edition works.
    T, f_orb = calc.update_Tforb(orbital_period_years=1.0)
    assert T == pytest.approx(1.0)
    assert f_orb == pytest.approx(1.0 / 31557600)


# ── cosmo_calc ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "z, expected",
    [
        (0.3056, (1471.4151534517296, 1118.093272697606, 4.184945521722361)),
        (0.1, (445.74269025228597, 405.22062750207806, 1.7859682210558636)),
        (1.0, (5872.070129475956, 2795.08887461239, 7.117149846537508)),
    ],
)
def test_cosmo_calc_known_redshift(z, expected):
    dl_mpc, dcmr_mpc, kpc_da = calc.cosmo_calc(z)
    exp_dl, exp_dcmr, exp_kpc = expected
    assert dl_mpc == pytest.approx(exp_dl, rel=1e-6)
    assert dcmr_mpc == pytest.approx(exp_dcmr, rel=1e-6)
    assert kpc_da == pytest.approx(exp_kpc, rel=1e-6)


def test_cosmo_calc_negative_redshift_rejected():
    with pytest.raises(calc.InvalidParameterError) as excinfo:
        calc.cosmo_calc(-0.5)
    assert "redshift" in str(excinfo.value)
