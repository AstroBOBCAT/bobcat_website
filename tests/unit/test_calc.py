"""
Tests for BOBcat_utils/calc.py.

Mass-related functions (Mc_calc, Mtot_calc, mu_calc, q_calc, find_m1_m2,
update_*) take/return masses as log10(Msun), converting internally via
10**m before doing linear-space arithmetic. This differs from the retired
Old_stuff/*.py scripts, which took linear masses -- expected values below
are derived from calc.py's own equations (verified independently in
Python), not carried over from the old tests.
"""
import pytest

from BOBcat_utils import calc


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
    # Given both m1 and m2 (log10), they're returned in log10
    # (larger mass first).
    m1, m2 = calc.find_m1_m2(primary_mass_log10=1.0, secondary_mass_log10=0.0)
    assert m1 == pytest.approx(1.0)
    assert m2 == pytest.approx(0.0, abs=1e-12)


def test_find_m1_m2_from_mtot_and_q():
    m1, m2 = calc.find_m1_m2(total_mass_log10=1.041392685158225, mass_ratio=0.1)
    assert m1 == pytest.approx(1.0, rel=1e-6)
    assert m2 == pytest.approx(0.0, abs=1e-6)


def test_find_m1_m2_from_mc_and_mu():
    m1, m2 = calc.find_m1_m2(chirp_mass_log10=0.39172146296835497, reduced_mass_log10=-0.04139268515822506)
    assert m1 == pytest.approx(1.0, rel=1e-6)
    assert m2 == pytest.approx(0.0, abs=1e-6)


def test_find_m1_m2_insufficient_params_raises_runtimeerror():
    with pytest.raises(RuntimeError) as excinfo:
        calc.find_m1_m2(primary_mass_log10=1.0)
    assert "at least two mass values" in str(excinfo.value)


def test_find_m1_m2_mc_too_large_for_mtot_raises_runtimeerror():
    with pytest.raises(RuntimeError):
        calc.find_m1_m2(chirp_mass_log10=2.0, total_mass_log10=1.0)


# ── update_Mc / update_Mtot / update_mu / update_q ──────────────────────────

def test_update_mc_within_tolerance_keeps_given():
    given = 0.39172146296835497
    assert calc.update_Mc(1.0, 0.0, chirp_mass_log10=given) == pytest.approx(given)


def test_update_mc_none_given_uses_calculated():
    assert calc.update_Mc(1.0, 0.0, chirp_mass_log10=None) == pytest.approx(
        calc.Mc_calc(1.0, 0.0)
    )


def test_update_mc_outside_tolerance_recomputes():
    # default tolerance is 1e5 (log10 solar masses), so a wildly-off given
    # value gets replaced by the calculated one.
    result = calc.update_Mc(1.0, 0.0, chirp_mass_log10=1e6)
    assert result == pytest.approx(calc.Mc_calc(1.0, 0.0))


def test_update_q_within_tolerance_keeps_given():
    assert calc.update_q(1.0, 0.0, mass_ratio=0.1) == pytest.approx(0.1)


def test_update_q_outside_tolerance_recomputes():
    # default tolerance is 0.01; 0.5 is far from the true q of 0.1
    assert calc.update_q(1.0, 0.0, mass_ratio=0.5) == pytest.approx(0.1)


# ── strain_calc ──────────────────────────────────────────────────────────────

def test_strain_calc_known_value():
    # Mc is now given as log10(Msun): log10(7.9e8) = 8.8976270912904414
    strain = calc.strain_calc(8.8976270912904414, 85, 60.4e-9)
    assert strain == pytest.approx(7.269388639002558e-15)


def test_strain_calc_bad_params_raises_runtimeerror():
    # Mc must be numeric (10**Mc happens before the type check),
    # so probe the check with bad Dl/f_grav instead.
    with pytest.raises(RuntimeError) as excinfo:
        calc.strain_calc(8.0, "b", 5)
    assert str(excinfo.value) == (
        "Arguments given are incorrect. 3 numerical values needed (Mc, Dl, f_grav)"
    )


# ── freq_calc ────────────────────────────────────────────────────────────────

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


def test_freq_calc_nothing_given_raises_runtimeerror():
    with pytest.raises(RuntimeError):
        calc.freq_calc()


def test_freq_calc_all_wrong_type_raises_typeerror():
    with pytest.raises(TypeError):
        calc.freq_calc(
            orbital_period_years="a", orbital_frequency_hz="b", gw_frequency_hz="c"
        )


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
