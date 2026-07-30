import math

import numpy as np
import sympy as sp
from pandas import isnull


"""
BOBcat calc library -- sympy edition.

Drop-in alternate to calc.py: same function behavior, argument order,
and unit conventions (mass parameters other than q are passed as
log10 solar masses), so `from BOBcat_utils import calc_sympy as calc`
works unchanged for positional callers. Parameter names are more
descriptive than calc.py's single-letter/short names (see each
docstring for the calc.py-equivalent short name), and every public
function is type-hinted.

What is different:

  * find_m1_m2() and q_limit() no longer use hand-derived closed-form
    branches (including the long complex-radical chirp-mass formulas).
    All six mass parameters are defined once as symbolic relations in
    m1 and m2, and sympy solves whichever pair of relations the caller
    provides. One solver replaces fifteen elif branches.

  * Errors are raised as subclasses of RuntimeError/TypeError (so
    existing `except` clauses still catch them) with messages that name
    the parameters given, the constraint violated, and what to fix.
    Nothing in this module prints and calls exit().

  * The forward calculators (Mc_calc, Mtot_calc, mu_calc, q_calc) are
    generated from the same symbolic relations used by the solver, so
    the definitions live in exactly one place.
"""


###########################
#  CONSTANTS
###########################

s_per_year = 31557600  # From IAU website (31.5576 Ms = 365.25 d), matching calc.py

G = 4.5170e-48  # Gravitational constant in units of Mpc^3 M_solar^-1 s^-2

c_Mpc_s = 9.7146e-15  # Speed of light in units of Mpc s^-1


###########################
#  ERRORS
###########################

class CalcError(Exception):
    """Base class for all errors raised by this module."""


class InsufficientParametersError(CalcError, RuntimeError):
    """Too few parameters were provided to determine the requested values."""


class InconsistentParametersError(CalcError, RuntimeError):
    """The provided parameters cannot describe a physical binary together."""


class InvalidParameterError(CalcError, TypeError):
    """A parameter has the wrong type or an unphysical value."""


def _require_number(
    name: str,
    value: float | None,
    description: str,
    allow_none: bool = True,
) -> float | None:
    """Return value unchanged if it is None (when allowed) or a real number;
    otherwise raise InvalidParameterError naming the argument."""
    if value is None and allow_none:
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise InvalidParameterError(
            f"{name} ({description}) must be a number"
            f"{' or None' if allow_none else ''}, "
            f"but got {type(value).__name__} {value!r}."
        )
    if isinstance(value, float) and math.isnan(value):
        return None if allow_none else value
    return value


###########################
#  SYMBOLIC MASS RELATIONS
###########################

# Deliberately no positivity assumptions: for some parameter pairs the
# solutions are cubics whose real roots sympy cannot prove positive
# (casus irreducibilis) and would silently drop. Physicality is checked
# numerically in find_m1_m2 instead.
_m1, _m2 = sp.symbols("m1 m2")

# Forward definitions of the derived mass parameters in terms of m1, m2.
_Mtot_expr = _m1 + _m2
_q_expr = _m2 / _m1                                   # convention: 0 < q <= 1
_mu_expr = _m1 * _m2 / (_m1 + _m2)
_Mc_expr = ((_m1 * _m2) ** 3 / (_m1 + _m2)) ** sp.Rational(1, 5)

# The same definitions, rearranged into polynomial residuals (expr == 0)
# so that sympy solves them without fractional powers.
_RESIDUALS = {
    "m1":   lambda v: _m1 - v,
    "m2":   lambda v: _m2 - v,
    "Mtot": lambda v: _m1 + _m2 - v,
    "q":    lambda v: _m2 - v * _m1,
    "mu":   lambda v: _m1 * _m2 - v * (_m1 + _m2),
    "Mc":   lambda v: (_m1 * _m2) ** 3 - v ** 5 * (_m1 + _m2),
}

# Which parameters carry mass units (and therefore arrive as log10 M_sun
# and participate in rescaling); q is dimensionless.
_MASS_LIKE = ("m1", "m2", "Mtot", "Mc", "mu")

# Pair-selection order matching the elif chain in calc.py, so that when
# more than two parameters are supplied both modules use the same pair.
_PAIR_PRECEDENCE = [
    ("m1", "m2"), ("m1", "Mtot"), ("m2", "Mtot"),
    ("m1", "q"), ("m2", "q"), ("q", "mu"),
    ("m1", "mu"), ("m2", "mu"), ("Mtot", "q"),
    ("q", "Mc"), ("Mtot", "mu"), ("Mc", "mu"),
    ("Mtot", "Mc"), ("m1", "Mc"), ("m2", "Mc"),
]

# Largest chirp mass a binary of total mass Mtot can have, reached at
# q = 1:  Mc/Mtot = (1/4)**(3/5) ~= 0.43528.
MC_TO_MTOT_MAX = float(sp.Rational(1, 4) ** sp.Rational(3, 5))

_PARAM_DESCRIPTIONS = {
    "m1": "primary mass, log10 M_sun",
    "m2": "secondary mass, log10 M_sun",
    "Mtot": "total mass, log10 M_sun",
    "q": "mass ratio m2/m1, dimensionless",
    "Mc": "chirp mass, log10 M_sun",
    "mu": "reduced mass, log10 M_sun",
}


def _explain_no_solution(pair: tuple[str, str], values: dict) -> str:
    """Build a message saying why the chosen parameter pair admits no
    physical (real, positive) m1 and m2."""
    given = ", ".join(f"{name}={values[name]:.6g} (linear M_sun)"
                      if name != "q" else f"q={values[name]:.6g}"
                      for name in pair)
    hints = {
        frozenset(("Mtot", "Mc")):
            f"a binary of total mass Mtot can have a chirp mass of at most "
            f"{MC_TO_MTOT_MAX:.5f}*Mtot (equal-mass case), i.e. "
            f"Mc <= {MC_TO_MTOT_MAX * values.get('Mtot', float('nan')):.6g} M_sun here",
        frozenset(("Mtot", "mu")):
            f"the reduced mass can be at most Mtot/4 (equal-mass case), i.e. "
            f"mu <= {values.get('Mtot', float('nan')) / 4:.6g} M_sun here",
        frozenset(("Mc", "mu")):
            f"the reduced mass can be at most (1/4)**(2/5)*Mc; "
            f"check that both values describe the same system",
        frozenset(("m1", "mu")):
            "the reduced mass must be smaller than either component mass",
        frozenset(("m2", "mu")):
            "the reduced mass must be smaller than either component mass",
    }
    hint = hints.get(frozenset(pair),
                     "no real, positive component masses satisfy both values")
    return (f"Inconsistent mass parameters: {given}. "
            f"No physical solution for (m1, m2) exists because {hint}. "
            f"Remember that mass-like inputs are log10 solar masses.")


##################

def find_m1_m2(
    primary_mass_log10: float | None = None,
    secondary_mass_log10: float | None = None,
    total_mass_log10: float | None = None,
    mass_ratio: float | None = None,
    chirp_mass_log10: float | None = None,
    reduced_mass_log10: float | None = None,
) -> tuple[float, float]:
    '''
    Find m1 and m2 for a binary system given at least two of the six
    common mass parameters (m1, m2, Mtot, q, Mc, mu).

    Inputs (all default None):

        primary_mass_log10 (m1), secondary_mass_log10 (m2),
        total_mass_log10 (Mtot), chirp_mass_log10 (Mc),
        reduced_mass_log10 (mu) = masses in log10 solar masses
        mass_ratio (q) = mass ratio m2/m1, dimensionless

    Outputs:

        m1, m2 = component masses in log10 solar masses, ordered so
                 that m1 >= m2 (i.e. q = m2/m1 <= 1).

    Instead of a chain of hand-derived closed forms, the two provided
    parameters are matched against their defining relations and sympy
    solves the resulting polynomial system for m1 and m2. Physically
    impossible combinations raise InconsistentParametersError with an
    explanation; fewer than two parameters raise
    InsufficientParametersError.
    '''
    m1, m2 = primary_mass_log10, secondary_mass_log10
    Mtot, q = total_mass_log10, mass_ratio
    Mc, mu = chirp_mass_log10, reduced_mass_log10

    raw = {"m1": m1, "m2": m2, "Mtot": Mtot, "q": q, "Mc": Mc, "mu": mu}
    for name, value in raw.items():
        raw[name] = _require_number(name, value, _PARAM_DESCRIPTIONS[name])

    # Convert log10 masses to linear solar masses; q stays as given.
    values = {}
    for name, value in raw.items():
        if value is None:
            continue
        values[name] = 10.0 ** value if name in _MASS_LIKE else float(value)

    if "q" in values and values["q"] <= 0:
        raise InvalidParameterError(
            f"q (mass ratio) must be positive, but got q={values['q']:.6g}. "
            f"The BOBcat convention is 0 < q <= 1 with q = m2/m1."
        )

    if len(values) < 2:
        provided = ", ".join(values) if values else "none"
        raise InsufficientParametersError(
            f"Not enough mass parameters to calculate m1 and m2: need at "
            f"least two of (m1, m2, Mtot, q, Mc, mu), but got {provided}. "
            f"Provide at least two mass values."
        )

    # Both component masses given: nothing to solve.
    if "m1" in values and "m2" in values:
        m1_lin, m2_lin = values["m1"], values["m2"]
    else:
        # Pick the first fully-provided pair in calc.py's precedence order.
        pair = next(p for p in _PAIR_PRECEDENCE
                    if p[0] in values and p[1] in values)

        # Rescale mass-like values to O(1) so the polynomial solve is
        # well conditioned, then undo the scaling on the way out.
        scale = max((values[n] for n in pair if n in _MASS_LIKE), default=1.0)
        equations = []
        for name in pair:
            v = values[name] / scale if name in _MASS_LIKE else values[name]
            equations.append(_RESIDUALS[name](sp.Float(v)))

        solutions = sp.solve(equations, [_m1, _m2], dict=True)

        # Check if solutions are physical. Certain combinations of parameters
        # may yield complex solutions for m1, m2. This block disregards them
        # and stores only physical solutions, within a tolerance of 1e-9
        # (to account for floating point errors? unclear why such a lax
        # tolerance is used).
        physical = []
        for sol in solutions:
            try:
                c1, c2 = complex(sol[_m1]), complex(sol[_m2])
            except (TypeError, KeyError):
                continue
            if (abs(c1.imag) <= 1e-9 * abs(c1) and c1.real > 0 and
                    abs(c2.imag) <= 1e-9 * abs(c2) and c2.real > 0):
                physical.append((c1.real * scale, c2.real * scale))

        if not physical:
            raise InconsistentParametersError(_explain_no_solution(pair, values))

        # Solutions come in (m1, m2)/(m2, m1) mirror pairs for symmetric
        # parameter sets; prefer the one already ordered m1 >= m2.
        physical.sort(key=lambda s: s[0] - s[1], reverse=True)
        m1_lin, m2_lin = physical[0]

    # Enforce the q <= 1 convention: m1 is always the larger mass.
    if m2_lin > m1_lin:
        m1_lin, m2_lin = m2_lin, m1_lin

    return float(np.log10(m1_lin)), float(np.log10(m2_lin))


# Fast numeric versions of the forward relations, generated once from
# the symbolic definitions above.
_Mc_lin = sp.lambdify((_m1, _m2), _Mc_expr, "numpy")
_Mtot_lin = sp.lambdify((_m1, _m2), _Mtot_expr, "numpy")
_mu_lin = sp.lambdify((_m1, _m2), _mu_expr, "numpy")


def _log_mass_pair(
    func_name: str,
    primary_mass_log10: float,
    secondary_mass_log10: float,
) -> tuple[float, float]:
    """Validate a (log10 m1, log10 m2) pair and return linear masses."""
    _require_number("m1", primary_mass_log10, _PARAM_DESCRIPTIONS["m1"], allow_none=False)
    _require_number("m2", secondary_mass_log10, _PARAM_DESCRIPTIONS["m2"], allow_none=False)
    return 10.0 ** primary_mass_log10, 10.0 ** secondary_mass_log10


def Mc_calc(primary_mass_log10: float, secondary_mass_log10: float) -> float:
    '''
    Calculate the chirp mass of a system given two masses.

    Inputs:  primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
    Outputs: Mc = chirp mass, log10 solar masses
    '''
    m1_lin, m2_lin = _log_mass_pair("Mc_calc", primary_mass_log10, secondary_mass_log10)
    return float(np.log10(_Mc_lin(m1_lin, m2_lin)))


def Mtot_calc(primary_mass_log10: float, secondary_mass_log10: float) -> float:
    '''
    Calculate the total mass of a system given two masses.

    Inputs:  primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
    Outputs: Mtot = total mass, log10 solar masses
    '''
    m1_lin, m2_lin = _log_mass_pair("Mtot_calc", primary_mass_log10, secondary_mass_log10)
    return float(np.log10(_Mtot_lin(m1_lin, m2_lin)))


def mu_calc(primary_mass_log10: float, secondary_mass_log10: float) -> float:
    '''
    Calculate the reduced mass of a system given two masses.

    Inputs:  primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
    Outputs: mu = reduced mass, log10 solar masses
    '''
    m1_lin, m2_lin = _log_mass_pair("mu_calc", primary_mass_log10, secondary_mass_log10)
    return float(np.log10(_mu_lin(m1_lin, m2_lin)))


def q_calc(primary_mass_log10: float, secondary_mass_log10: float) -> float:
    '''
    Calculate the mass ratio of a system given two masses.
    Mass ratio is here defined 0 < q <= 1, so the argument order
    does not matter.

    Inputs:  primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
    Outputs: q = mass ratio, dimensionless
    '''
    m1_lin, m2_lin = _log_mass_pair("q_calc", primary_mass_log10, secondary_mass_log10)
    return min(m1_lin, m2_lin) / max(m1_lin, m2_lin)


def q_limit(chirp_mass_log10: float, total_mass_log10: float) -> tuple[float, float]:
    '''
    Convert a (chirp mass, total mass) pair to the two mass-ratio roots
    of the defining relation Mc = Mtot * (q / (1+q)**2)**(3/5), without
    anyone having to do the quadratic formula by hand: sympy solves the
    quadratic  r*q**2 + (2r - 1)*q + r = 0  with r = (Mc/Mtot)**(5/3).

    Go in peace.

    Inputs:

        chirp_mass_log10 (Mc) = chirp mass (e.g. an upper limit from a
             CW search), log10 solar masses
        total_mass_log10 (Mtot) = total mass of the SMBH binary, log10
             solar masses

    Outputs:

        q = the physical mass ratio root (0 < q <= 1)
        multiplier = the reciprocal root (>= 1)

    Unlike calc.py this never prints and exit()s: if Mc is too large
    for Mtot it raises InconsistentParametersError instead, so callers
    (and the website) survive bad inputs.
    '''
    Mc, Mtot = chirp_mass_log10, total_mass_log10

    _require_number("Mc", Mc, _PARAM_DESCRIPTIONS["Mc"], allow_none=False)
    _require_number("Mtot", Mtot, _PARAM_DESCRIPTIONS["Mtot"], allow_none=False)

    Mc_lin = 10.0 ** Mc
    Mtot_lin = 10.0 ** Mtot

    ratio = Mc_lin / Mtot_lin
    if ratio > MC_TO_MTOT_MAX:
        raise InconsistentParametersError(
            f"The inputs imply a mass ratio q > 1: Mc={Mc_lin:.6g} M_sun is "
            f"{ratio:.4f} of Mtot={Mtot_lin:.6g} M_sun, above the physical "
            f"maximum of {MC_TO_MTOT_MAX:.5f} (an equal-mass binary). "
            f"Remember q is defined 0 < q <= 1. If these are results from a "
            f"CW upper-limit run, they are not constraining on q."
        )

    qs = sp.symbols("q", positive=True)
    r = sp.Float(ratio ** (5.0 / 3.0))
    roots = sp.solve(sp.Eq(r * (1 + qs) ** 2, qs), qs)
    roots = sorted(float(root) for root in roots)

    q, multiplier = roots[0], roots[-1]
    return q, multiplier

# This is the BOBcat SMBHB Candidate Mass Value Calculator. It will
# read provided inputs of mass quantities and can calculate unknown
# mass quantities. Currently it is equipped to calculate Mass 1,
# Mass 2, Total Mass, Mass Ratio, Chirp Mass, and Reduced Mass.

# As of right now, this calculator only fills in empty values; it is
# not a judge of erroneous/incongruent inputs. If the inputs were
# found via different methods/models, try entering only the inputs
# that used a consistent model.


def mass_val_calc(
    primary_mass_log10: float | None = None,
    secondary_mass_log10: float | None = None,
    total_mass_log10: float | None = None,
    chirp_mass_log10: float | None = None,
    reduced_mass_log10: float | None = None,
    mass_ratio: float | None = None,
) -> list:
    """
    This is the BOBcat SMBHB mass value calculator! It will calculate
    estimates of Mass 1, Mass 2, Total Mass, Mass Ratio, Chirp Mass,
    and Reduced Mass (in solar masses) given known mass parameters of
    the binary candidate (in solar masses). To successfully calculate
    the unknown values, at least two known parameters are needed as
    inputs.

    Choose two of any inputs from the list below.
    All values below are the outputs.
    Units for all: Solar Masses

    primary_mass_log10 (m1) = Larger Mass
    secondary_mass_log10 (m2) = Smaller Mass
    total_mass_log10 (Mtot) = Total Mass
    mass_ratio (q) = Mass Ratio
    chirp_mass_log10 (Mc) = Chirp Mass
    reduced_mass_log10 (mu) = Reduced Mass

    """
    m1, m2 = primary_mass_log10, secondary_mass_log10
    Mtot, Mc, mu, q = total_mass_log10, chirp_mass_log10, reduced_mass_log10, mass_ratio

    mass_array = [m1, m2, Mtot, Mc, mu, q]

    known = sum(1 for value in mass_array if not isnull(value))
    if known < 2:
        print(f"At least two of the inputs (m1, m2, Mtot, Mc, mu, q) must be "
              f"known to calculate the other values; got {known}. "
              f"Returning the inputs unchanged.")
        return mass_array

    mass_array, updated_masses = update_masses(m1, m2, Mtot, Mc, mu, q)

    return mass_array


###############
#  UPDATE (SELF-CONSISTENCY) FUNCTIONS
###############

def _reconcile(given: float | None, calculated: float, tolerance: float) -> float:
    """Return `calculated` if `given` is missing or differs from it by
    at least `tolerance`; otherwise keep `given`."""
    if isnull(given) or abs(given - calculated) >= tolerance:
        return calculated
    return given


def update_m1(
    primary_mass_log10: float | None = None,
    secondary_mass_log10: float | None = None,
    total_mass_log10: float | None = None,
    mass_ratio: float | None = None,
    chirp_mass_log10: float | None = None,
    reduced_mass_log10: float | None = None,
    tolerance: float = 1e5,
) -> float:
    '''
    Update the mass 1 value given to that calculated if the tolerance
    is not met. If no m1 is passed, or it differs from the value
    implied by the other parameters by at least `tolerance`, the
    calculated value (log10 solar masses, from find_m1_m2) is
    returned instead.

    Inputs: as find_m1_m2, plus
        tolerance = replacement threshold, default 1e5

    Outputs:
        m1 = mass of first binary object
    '''
    m1, m2 = primary_mass_log10, secondary_mass_log10
    Mtot, q = total_mass_log10, mass_ratio
    Mc, mu = chirp_mass_log10, reduced_mass_log10

    m1_calced = find_m1_m2(m1, m2, Mtot, q, Mc, mu)[0]
    return _reconcile(m1, m1_calced, tolerance)


def update_m2(
    primary_mass_log10: float | None = None,
    secondary_mass_log10: float | None = None,
    total_mass_log10: float | None = None,
    mass_ratio: float | None = None,
    chirp_mass_log10: float | None = None,
    reduced_mass_log10: float | None = None,
    tolerance: float = 1e5,
) -> float:
    '''
    Update the mass 2 value given to that calculated if the tolerance
    is not met. If no m2 is passed, or it differs from the value
    implied by the other parameters by at least `tolerance`, the
    calculated value (log10 solar masses, from find_m1_m2) is
    returned instead.

    Inputs: as find_m1_m2, plus
        tolerance = replacement threshold, default 1e5

    Outputs:
        m2 = mass of second binary object
    '''
    m1, m2 = primary_mass_log10, secondary_mass_log10
    Mtot, q = total_mass_log10, mass_ratio
    Mc, mu = chirp_mass_log10, reduced_mass_log10

    m2_calced = find_m1_m2(m1, m2, Mtot, q, Mc, mu)[1]
    return _reconcile(m2, m2_calced, tolerance)


def update_Mc(
    primary_mass_log10: float,
    secondary_mass_log10: float,
    chirp_mass_log10: float | None = None,
    tolerance: float = 1e5,
) -> float:
    '''
    Update the chirp mass value given to that calculated (from m1 and
    m2, both log10 solar masses) if the tolerance is not met.

    Inputs:
        primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
        chirp_mass_log10 (Mc) = chirp mass, log10 solar masses, default None
        tolerance = replacement threshold, default 1e5

    Outputs:
        Mc = chirp mass, log10 solar masses
    '''
    return _reconcile(chirp_mass_log10, Mc_calc(primary_mass_log10, secondary_mass_log10), tolerance)


def update_Mtot(
    primary_mass_log10: float,
    secondary_mass_log10: float,
    total_mass_log10: float | None = None,
    tolerance: float = 1e5,
) -> float:
    '''
    Update the total mass value given to that calculated (from m1 and
    m2, both log10 solar masses) if the tolerance is not met.

    Inputs:
        primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
        total_mass_log10 (Mtot) = total mass, log10 solar masses, default None
        tolerance = replacement threshold, default 1e5

    Outputs:
        Mtot = total mass, log10 solar masses
    '''
    return _reconcile(total_mass_log10, Mtot_calc(primary_mass_log10, secondary_mass_log10), tolerance)


def update_mu(
    primary_mass_log10: float,
    secondary_mass_log10: float,
    reduced_mass_log10: float | None = None,
    tolerance: float = 1e5,
) -> float:
    '''
    Update the reduced mass value given to that calculated (from m1
    and m2, both log10 solar masses) if the tolerance is not met.

    Inputs:
        primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
        reduced_mass_log10 (mu) = reduced mass, log10 solar masses, default None
        tolerance = replacement threshold, default 1e5

    Outputs:
        mu = reduced mass, log10 solar masses
    '''
    return _reconcile(reduced_mass_log10, mu_calc(primary_mass_log10, secondary_mass_log10), tolerance)


def update_q(
    primary_mass_log10: float,
    secondary_mass_log10: float,
    mass_ratio: float | None = None,
    tolerance: float = 0.01,
) -> float:
    '''
    Update the mass ratio value given to that calculated (from m1 and
    m2, both log10 solar masses) if the tolerance is not met.

    Inputs:
        primary_mass_log10 (m1), secondary_mass_log10 (m2) =
             component masses, log10 solar masses
        mass_ratio (q) = mass ratio, dimensionless, default None
        tolerance = replacement threshold, default 0.01

    Outputs:
        q = mass ratio, dimensionless
    '''
    return _reconcile(mass_ratio, q_calc(primary_mass_log10, secondary_mass_log10), tolerance)


def update_masses(
    primary_mass_log10: float | None,
    secondary_mass_log10: float | None,
    total_mass_log10: float | None,
    chirp_mass_log10: float | None,
    reduced_mass_log10: float | None,
    mass_ratio: float | None,
) -> tuple[list, list]:
    '''
    Update all six of the mass values used to fully describe a binary
    system so they are mutually consistent. NOTE: this function only
    uses the default tolerances of the individual update_* functions;
    tolerances cannot be set here.

    Inputs:
        primary_mass_log10 (m1), secondary_mass_log10 (m2),
        total_mass_log10 (Mtot), chirp_mass_log10 (Mc),
        reduced_mass_log10 (mu) = masses, log10 solar masses (or None)
        mass_ratio (q) = mass ratio, dimensionless (or None)

    Outputs:
        ([m1, m2, Mtot, Mc, mu, q] after updating,
         list of the names of the values that changed)
    '''
    m1, m2 = primary_mass_log10, secondary_mass_log10
    Mtot, Mc, mu, q = total_mass_log10, chirp_mass_log10, reduced_mass_log10, mass_ratio

    m1_updated = update_m1(m1, m2, Mtot, q, Mc, mu)
    m2_updated = update_m2(m1, m2, Mtot, q, Mc, mu)
    Mtot_updated = update_Mtot(m1, m2, Mtot)
    q_updated = update_q(m1, m2, q)
    Mc_updated = update_Mc(m1, m2, Mc)
    mu_updated = update_mu(m1, m2, mu)

    originals = {"m1": m1, "m2": m2, "Mtot": Mtot, "q": q, "Mc": Mc, "mu": mu}
    updates = {"m1": m1_updated, "m2": m2_updated, "Mtot": Mtot_updated,
               "q": q_updated, "Mc": Mc_updated, "mu": mu_updated}
    updated_masses = [name for name in originals
                      if updates[name] != originals[name]]

    return ([m1_updated, m2_updated, Mtot_updated,
             Mc_updated, mu_updated, q_updated], updated_masses)


###########################
#  STRAIN CALCULATIONS
###########################

def strain_calc(
    chirp_mass_log10: float,
    luminosity_distance_mpc: float,
    gw_frequency_hz: float,
) -> float:
    '''
    Calculate strain amplitude using the NANOGrav "standard" strain
    equation as used in e.g. 2020ApJ...900..102A (the NANOGrav GW
    search paper that targeted 3C66B), accounting for self-consistent
    use of units.

    Inputs:
        chirp_mass_log10 (Mc) = chirp mass, units = log10(M_solar)
        luminosity_distance_mpc (Dl) = luminosity distance, units = Mpc
        gw_frequency_hz (f_grav) = gravitational wave frequency, units = s^-1 (Hz)

    Outputs:
        h = GW characteristic strain, dimensionless

    '''
    Mc, Dl, f_grav = chirp_mass_log10, luminosity_distance_mpc, gw_frequency_hz

    _require_number("Mc", Mc, "chirp mass, log10 M_sun", allow_none=False)
    for name, value, description in (
            ("Dl", Dl, "luminosity distance, Mpc"),
            ("f_grav", f_grav, "gravitational wave frequency, Hz")):
        _require_number(name, value, description, allow_none=False)
        if value <= 0:
            raise InvalidParameterError(
                f"{name} ({description}) must be positive, but got "
                f"{value!r}; the strain equation is only meaningful for "
                f"positive {name}."
            )

    # Convert mass from log10 to linear solar masses.
    Mc = 10.0 ** Mc

    # Equation from https://iopscience.iop.org/article/10.3847/1538-4357/ababa1/pdf
    # and http://www.physics.usu.edu/Wheeler/GenRel2013/Notes/GravitationalWaves.pdf
    h = 2 * (((np.pi * f_grav) ** (2 / 3)) * ((G * Mc) ** (5 / 3))) / ((c_Mpc_s ** 4) * Dl)
    return h


def tgw_calc(
    semimajor_axis_pc: float,
    total_mass_log10: float,
    reduced_mass_log10: float,
) -> float:
    '''
    Calculate time to coalescence based on purely GW radiation.
    Assumed e = 0, general relativity.

    Inputs:
        semimajor_axis_pc (a) = semi-major axis in parsecs.
        total_mass_log10 (mtot) = log10( total mass in Msun units )
        reduced_mass_log10 (mu) = log10( reduced mass in Msun units )

    Outputs:
        t_gw = time to coalescence in years

    '''
    a, mtot, mu = semimajor_axis_pc, total_mass_log10, reduced_mass_log10

    for name, value, description in (
            ("a", a, "semi-major axis, pc"),
            ("mtot", mtot, "total mass, log10 M_sun"),
            ("mu", mu, "reduced mass, log10 M_sun")):
        _require_number(name, value, description, allow_none=False)
    if a <= 0:
        raise InvalidParameterError(
            f"a (semi-major axis, pc) must be positive, but got {a!r}."
        )

    # Convert semi-major axis to Mpc and expand log mass values.
    a_Mpc = a * 1e-6
    mtot_lin = 10.0 ** mtot
    mu_lin = 10.0 ** mu

    # Equation from Peters 1964 or from Maggiore book.
    t_gw = (5 * c_Mpc_s ** 5 * a_Mpc ** 4) / (256 * G ** 3 * mtot_lin ** 2 * mu_lin)
    return t_gw / s_per_year


###########################
#  KEPLER'S LAWS
###########################

def kepler_semimajor(orbital_period_years: float, total_mass_log10: float) -> float:
    """
    Calculate binary semi-major axis from Kepler's third law.

    Parameters
    ----------
    orbital_period_years : float
        Orbital period in years.

    total_mass_log10 : float
        log10(total binary mass in solar masses).

    Returns
    -------
    float
        Semi-major axis in parsecs.
    """
    period_years, mtot = orbital_period_years, total_mass_log10

    _require_number("period_years", period_years, "orbital period, years", allow_none=False)
    _require_number("mtot", mtot, "total mass, log10 M_sun", allow_none=False)
    if period_years <= 0:
        raise InvalidParameterError(
            f"period_years (orbital period, years) must be positive, "
            f"but got {period_years!r}."
        )

    period_seconds = period_years * s_per_year
    mtot_lin = 10.0 ** mtot

    # Kepler's third law:
    # a^3 = G M P^2 / 4 pi^2
    a = (G * mtot_lin * period_seconds ** 2 / (4.0 * math.pi ** 2)) ** (1.0 / 3.0)

    # Convert Mpc to pc
    return a * 1.0e6


def kepler_period(semimajor_axis_pc: float, total_mass_log10: float) -> float:
    """
    Calculate binary orbital period from Kepler's third law.

    Parameters
    ----------
    semimajor_axis_pc : float
        Binary semi-major axis in parsecs.

    total_mass_log10 : float
        log10(total binary mass in solar masses).

    Returns
    -------
    float
        Orbital period in years.
    """
    a_pc, mtot = semimajor_axis_pc, total_mass_log10

    _require_number("a_pc", a_pc, "semi-major axis, pc", allow_none=False)
    _require_number("mtot", mtot, "total mass, log10 M_sun", allow_none=False)
    if a_pc <= 0:
        raise InvalidParameterError(
            f"a_pc (semi-major axis, pc) must be positive, but got {a_pc!r}."
        )

    # a is converted from pc to Mpc because G is in Mpc^3 Msun^-1 s^-2.
    a = a_pc * 1.0e-6
    mtot_lin = 10.0 ** mtot

    # Kepler's third law:
    # P = sqrt(4 pi^2 a^3 / G M)
    period_seconds = math.sqrt((4.0 * math.pi ** 2 * a ** 3) / (G * mtot_lin))

    return period_seconds / s_per_year


###########################
#  FREQUENCY CONVERSION
###########################

def freq_calc(
    orbital_period_years: float | None = None,
    orbital_frequency_hz: float | None = None,
    gw_frequency_hz: float | None = None,
) -> list:
    """
    Read any of the orbital period in the source frame (in years), the
    orbital frequency in the source frame (in Hz), and the dominant
    gravitational wave frequency assuming near-circular orbits (in Hz)
    and calculate the values missing from the inputs. If all three are
    supplied they are returned unchanged.

    The conversion conventions are identical to calc.py:
    f_orb = 1/T and f_grav = 2*f_orb, with the IAU year (31.5576 Ms).

    Args:
        orbital_period_years (T) = orbital period, years
        orbital_frequency_hz (f_orb) = orbital frequency, Hz
        gw_frequency_hz (f_grav) = dominant gravitational wave frequency, Hz

    Returns:
        [f_orb, T, f_grav]
    """
    T = _require_number("T", orbital_period_years, "orbital period, years")
    f_orb = _require_number("f_orb", orbital_frequency_hz, "orbital frequency, Hz")
    f_grav = _require_number("f_grav", gw_frequency_hz, "GW frequency, Hz")

    if T is not None and f_orb is not None and f_grav is not None:
        return [f_orb, T, f_grav]

    if T is not None:
        T_sec = T * s_per_year
        if f_orb is None:
            f_orb = 1 / T_sec
        if f_grav is None:
            f_grav = 2 * f_orb
    elif f_orb is not None:
        T = 1 / f_orb / s_per_year
        if f_grav is None:
            f_grav = 2 * f_orb
    elif f_grav is not None:
        T = 2 / f_grav / s_per_year
        f_orb = 0.5 * f_grav
    else:
        raise InsufficientParametersError(
            "freq_calc() needs at least one of T (orbital period, years), "
            "f_orb (orbital frequency, Hz) or f_grav (GW frequency, Hz), "
            "but all three were None."
        )

    # From here, frequency values can be reinserted into the BOBcat
    # database.
    return [f_orb, T, f_grav]


def update_Tforb(
    orbital_period_years: float | None = None,
    orbital_frequency_hz: float | None = None,
    gw_frequency_hz: float | None = None,
    tolerance: float = 1e-5,
) -> tuple[float, float]:
    """
    Check the self-consistency of the orbital period T (years), the
    orbital frequency f_orb (Hz) and the GW frequency f_grav (Hz).
    Missing values, or values differing from those implied by the
    other inputs by at least `tolerance`, are replaced by the
    calculated ones.

    Returns:
        (T, f_orb)
    """
    f_orb_calced, T_calced, _ = freq_calc(orbital_period_years, orbital_frequency_hz, gw_frequency_hz)

    T = _reconcile(orbital_period_years, T_calced, tolerance)
    f_orb = _reconcile(orbital_frequency_hz, f_orb_calced, tolerance)

    return T, f_orb


###########################
#  COSMOLOGY FUNCTIONS
###########################

def cosmo_calc(
    redshift: float,
    hubble_constant: float = 70,
    omega_matter: float = 0.3,
    omega_vacuum: float = 0.000085,
) -> tuple[float, float, float]:
    """
    This is the BOBcat cosmological distance calculator. It was built
    upon the following: Cosmology calculator
    (www.astro.ucla.edu/~wright/CosmoCalc.html) ala Ned Wright
    (www.astro.ucla.edu/~wright) Cosmology calculator python version
    (www.astro.ucla.edu/~wright/CC.python) ala James Schombert
    (abyss.uoregon.edu/~js/)

    This version has been simplified to only include inputs necessary
    for the desired output array.

    Required input: redshift (z)
    Optional inputs: hubble_constant (H0), omega_matter (WM),
                      omega_vacuum (WV)

    Outputs: (luminosity distance in Mpc,
              comoving radial distance in Mpc,
              angular diameter distance scale in kpc/")

    By default, this calculator assumes a flat universe in line with
    the benchmark model. Other universes can be built via custom
    values of WM and WV.
    """
    z, H0, WM, WV = redshift, hubble_constant, omega_matter, omega_vacuum

    _require_number("z", z, "redshift", allow_none=False)
    _require_number("H0", H0, "Hubble constant, km/s/Mpc", allow_none=False)
    if z < 0:
        raise InvalidParameterError(
            f"z (redshift) must be non-negative for a cosmological source, "
            f"but got z={z!r}."
        )
    if H0 <= 0:
        raise InvalidParameterError(
            f"H0 (Hubble constant, km/s/Mpc) must be positive, but got "
            f"H0={H0!r}."
        )

    c = 299792.458           # speed of light, km/s
    h = H0 / 100.0
    WR = 4.165e-5 / (h * h)  # Omega(radiation), incl. 3 massless neutrinos
    WK = 1 - WM - WR - WV    # Omega(curvature)
    az = 1.0 / (1 + z)       # scale factor at the object's redshift

    # Comoving radial distance: integrate da/(a*adot) from az to 1,
    # midpoint rule with n points (identical to calc.py).
    n = 1000
    DCMR = 0.0
    for i in range(n):
        a = az + (1 - az) * (i + 0.5) / n
        adot = np.sqrt(WK + (WM / a) + (WR / (a * a)) + (WV * a * a))
        DCMR = DCMR + 1.0 / (a * adot)

    DCMR = (1.0 - az) * DCMR / n
    DCMR_Mpc = (c / H0) * DCMR

    # Tangential comoving distance.
    ratio = 1.00
    x = np.sqrt(abs(WK)) * DCMR
    if x > 0.1:
        if WK > 0:
            ratio = 0.5 * (np.exp(x) - np.exp(-x)) / x
        else:
            ratio = np.sin(x) / x
    else:
        y = x * x
        # Mirrors calc.py exactly: the series correction is applied only
        # for closed universes (WK < 0); otherwise ratio stays 1.0.
        if WK < 0:
            y = -y
            ratio = 1.0 + y / 6.0 + y * y / 120.0
    DCMT = ratio * DCMR

    # Angular diameter distance and scale.
    DA = az * DCMT
    DA_Mpc = (c / H0) * DA
    kpc_DA = DA_Mpc / 206.264806

    # Luminosity distance.
    DL = DA / (az * az)
    DL_Mpc = (c / H0) * DL

    return (DL_Mpc, DCMR_Mpc, kpc_DA)
