import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from django.utils import timezone

from BOBcat_utils import astrodb, calc
from mainpage.models import (
    BinaryModel,
    BinaryModelError,
    Bib,
    Candidate,
    ERROR_TYPE_CHOICES,
    EvidenceCategory,
    EvidenceSubcategory,
    ModelEvidence,
    ModelEvidenceWaveband,
    ObsPeriod,
    ObsPeriodError,
    WAVEBAND_CHOICES,
)

logger = logging.getLogger(__name__)

# BOBCAT_SHEET_KEY is set in .db_info (the project's env file, loaded via
# docker-compose's env_file:) alongside the other deployment settings; the
# literal string here is only a fallback for environments that don't set it.
DEFAULT_SHEET_KEY = os.environ.get(
    "BOBCAT_SHEET_KEY", "1DTFQ3KMg1qkonvCv6veT0TqLmC4hbdjUQ09_CQfVMoI"
)

DAYS_PER_YEAR = 365.25

PARAM_TO_FIELD = {
    "eccentricity": "eccentricity",
    "log(m1)": "m1",
    "log(m2)": "m2",
    "log(total mass)": "mtot",
    "log(chirp mass)": "mc",
    "log(reduced mass)": "mu",
    "q": "q",
    "inclination": "inclination",
    "semi-major axis": "semimajor_axis",
    "separation": "separation",
    "period epoch": "orb_period_epoch",
    "orbital period (earth frame)": "orb_period",
    "Summary/notes on source": "summary",
    "Caveats": "caveats",
    "Extension project": "ext_proj",
}

VALID_RANGES = {
    "eccentricity": (0, 1),
    "log(m1)": (4, 12),
    "log(m2)": (4, 12),
    "log(total mass)": (4, 12),
    "log(chirp mass)": (4, 12),
    "log(reduced mass)": (4, 12),
    "q": (0, 1),
    "inclination": (0, 90),
    "semi-major axis": (0, 1000),
    "separation": (0, 1000),
    "period epoch": (40000, 70000),
}

VALID_ERROR_TYPES = {et[0] for et in ERROR_TYPE_CHOICES}

# Sheet parameter names that carry an Error / Error type column pair.
_NUMERIC_PARAMS = [
    "eccentricity", "log(m1)", "log(m2)", "log(total mass)",
    "log(chirp mass)", "log(reduced mass)", "q", "inclination",
    "semi-major axis", "separation", "orbital period (earth frame)",
]

# When True, a sheet value for any of _NUMERIC_PARAMS is only used to fill
# a BinaryModel field (and, transitively, to calculate other fields from
# it) if that value has a "valid" associated error: either an Error value
# AND an Error type, or an Error type of "Assumed" (which may carry no
# explicit Error value). Values without a valid error are treated as if
# blank. See _row_has_valid_error().
STRICT_ERROR = True

EVIDENCE_CATEGORY_MAP = {
    # DB value → DB value (identity, for sheet values that already match)
    "spectral_line_variability": EvidenceCategory.SPECTRAL_LINE_VARIABILITY,
    "spectral_line_snapshot": EvidenceCategory.SPECTRAL_LINE_SNAPSHOT,
    "continuum_variability": EvidenceCategory.CONTINUUM_VARIABILITY,
    "spatially_resolved_offset_or_dual_agn": EvidenceCategory.SPATIALLY_RESOLVED_OFFSET_OR_DUAL_AGN,
    "pc_jet_morphology": EvidenceCategory.PC_JET_MORPHOLOGY,
    "kpc_jet_morphology": EvidenceCategory.KPC_JET_MORPHOLOGY,
    "host_galaxy": EvidenceCategory.HOST_GALAXY,
    "gravitational_wave": EvidenceCategory.GRAVITATIONAL_WAVE,
    "sed_feature": EvidenceCategory.SED_FEATURE,
    # Aliases used in Google Sheets / evidence-categories file
    "emission_line_variability": EvidenceCategory.SPECTRAL_LINE_VARIABILITY,
    "emission_line_snapshot": EvidenceCategory.SPECTRAL_LINE_SNAPSHOT,
    "continuum_flux_variations": EvidenceCategory.CONTINUUM_VARIABILITY,
    "spatially_resolved_offset_or_dual_active_nucleus": EvidenceCategory.SPATIALLY_RESOLVED_OFFSET_OR_DUAL_AGN,
    "pc_scale_jet_features": EvidenceCategory.PC_JET_MORPHOLOGY,
    "large_scale_jet_features": EvidenceCategory.KPC_JET_MORPHOLOGY,
    "kpc_scale_jet_features": EvidenceCategory.KPC_JET_MORPHOLOGY,
    "galaxy_features": EvidenceCategory.HOST_GALAXY,
    "gravitational_wave_emission": EvidenceCategory.GRAVITATIONAL_WAVE,
    "broad_band_sed": EvidenceCategory.SED_FEATURE,
}

# Canonical subcategories per category, seeded if the table is empty.
# Keys are the file/sheet category names; values map to DB EvidenceCategory
# via EVIDENCE_CATEGORY_MAP above.
EVIDENCE_SUBCATEGORIES = {
    "emission_line_variability": [
        "broad-line velocity shifts",
        "narrow-line velocity shifts",
    ],
    "emission_line_snapshot": [
        "multiple narrow-line peaks",
        "multiple broad-line peaks",
        "other abnormal blr (e.g. asymmetries)",
        "other abnormal nlr",
    ],
    "continuum_flux_variations": [
        "continuous light curve variation with periodicity",
        "discrete bursts with periodicity",
        "correlated multi-band variations",
    ],
    "spatially_resolved_offset_or_dual_active_nucleus": [
        "dual nuclei",
        "active nucleus offset from photo/kin center",
    ],
    "pc_scale_jet_features": [
        "helical structure",
        "time-resolved helical outflow",
        "cso/css source",
    ],
    "large_scale_jet_features": [
        "x/s/z/helical shaped sources",
        "spatial periodicity",
    ],
    "galaxy_features": [
        "morphological (tidal tails, asymmetry, etc)",
        "flat-cored galaxy/light deficit",
        "enhanced tidal disruption rates",
        "very massive galaxy",
        "other secondary merger indicators",
    ],
    "gravitational_wave_emission": [
        "pta: gw memory",
        "pta: continuous waves",
        "space: gw memory",
        "space: continuous waves",
    ],
    "broad_band_sed": [
        "n/a",
    ],
}

WAVEBAND_MAP = {
    "radio": "radio",
    "ir": "infrared",
    "optical": "optical",
    "uv": "UV",
    "x-ray": "x-ray",
    "xray": "x-ray",
    "gamma": "gamma-ray",
    "gamma-ray": "gamma-ray",
}

BINARY_MODEL_FIELDS = {f.name for f in BinaryModel._meta.get_fields()}

STRING_FIELDS = {"summary", "caveats", "ext_proj"}


# ---------------------------------------------------------------------------
# Evidence subcategory seeding
# ---------------------------------------------------------------------------

def seed_evidence_subcategories():
    """Populate EvidenceSubcategory table if it is empty."""
    if EvidenceSubcategory.objects.exists():
        return
    logger.info("Seeding EvidenceSubcategory table...")
    rows = []
    for file_cat, subcats in EVIDENCE_SUBCATEGORIES.items():
        db_category = EVIDENCE_CATEGORY_MAP[file_cat]
        for name in subcats:
            rows.append(EvidenceSubcategory(
                category=db_category,
                name=name[:50],
            ))
    EvidenceSubcategory.objects.bulk_create(rows, ignore_conflicts=True)
    logger.info("Seeded %d evidence subcategories", len(rows))


# ---------------------------------------------------------------------------
# Sheet fetching
# ---------------------------------------------------------------------------

def _csv_url(key: str) -> str:
    if not isinstance(key, str):
        raise TypeError("Sheet key must be a string")
    return f"https://docs.google.com/spreadsheet/ccc?key={key}&output=csv"


def _extract_sheet_key(url: str) -> str:
    return url.split("/")[5]


def get_model_list(key: str) -> pd.DataFrame:
    return pd.read_csv(_csv_url(key), dtype=str)


def get_parameter_sheet(sheet_url: str) -> pd.DataFrame:
    key = _extract_sheet_key(sheet_url)
    return pd.read_csv(
        _csv_url(key),
        usecols=["Name", "Value", "Error", "Error type"],
        dtype=str,
    )


# ---------------------------------------------------------------------------
# Bibcode extraction
# ---------------------------------------------------------------------------

def extract_bibcode(link: str) -> tuple[str, str]:
    """Return (scix_link, bibcode) from an ADS or SciX URL.

    DOI links (doi.org / dx.doi.org) are also accepted; the DOI itself is
    returned in the bibcode slot (resolving a DOI to a real bibcode would
    need the ADS API and a token).
    """
    link = str(link).strip()
    for domain in ("ui.adsabs", "scixplorer.org"):
        if domain in link:
            parts = link.rstrip("/").split("/")
            bibcode = parts[-1] if parts[-1] != "abstract" else parts[-2]
            bibcode = bibcode.replace("%26", "&") # Fixes A%26A URL code for A&A journal (and potentially others)
            scix_link = f"https://scixplorer.org/abs/{bibcode}"
            return scix_link, bibcode
    if "doi.org/" in link:
        doi = link.split("doi.org/", 1)[1].strip("/")
        return link, doi
    return link, ""


# ---------------------------------------------------------------------------
# Value helpers
# ---------------------------------------------------------------------------

_BLANK = frozenset({"", "nan", "--", "na", "n/a"})


def _safe_float(val) -> float | None:
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in _BLANK:
        return None
    try:
        f = float(val)
        return None if np.isnan(f) else f
    except (ValueError, TypeError):
        return None


def _is_blank(val) -> bool:
    if val is None:
        return True
    return str(val).strip().lower() in _BLANK


def _row_has_valid_error(indexed_df: pd.DataFrame, param: str) -> bool:
    """True if `param`'s row has an Error value and a recognized Error
    type, or an Error type of "Assumed" (which may carry no explicit
    value). Used both to decide whether to record an error (parse_errors)
    and, under STRICT_ERROR, whether to use the value at all
    (validate_and_fill)."""
    err_raw = _get_cell(indexed_df, param, "Error")
    etype_raw = _get_cell(indexed_df, param, "Error type")

    if _is_blank(etype_raw):
        return False
    etype_str = str(etype_raw).strip()
    etype_is_assumed = etype_str.lower() == "assumed"

    if _is_blank(err_raw) and not etype_is_assumed:
        return False

    etype_normalized = _ERROR_TYPE_ALIASES.get(etype_str.lower(), etype_str)
    if etype_normalized is not None and etype_normalized not in VALID_ERROR_TYPES:
        logger.warning("Unknown error type '%s' for %s, skipping", etype_str, param)
        return False
    return True


# ---------------------------------------------------------------------------
# Parsing a parameter sheet
# ---------------------------------------------------------------------------

def _index_param_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Trim template rows below the first NaN Name and index by Name."""
    if df["Name"].isna().any():
        nan_idx = df["Name"].isna().idxmax()
        df = df.iloc[:nan_idx]
    return df.set_index("Name")


def _get_cell(indexed_df: pd.DataFrame, name: str, col: str = "Value"):
    if name not in indexed_df.index:
        return None
    row = indexed_df.loc[name]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    return row[col] if col in row.index else None


# ---------------------------------------------------------------------------
# Validation & value filling
# ---------------------------------------------------------------------------

def validate_and_fill(indexed_df: pd.DataFrame, lum_dist: float | None = None) -> tuple[dict, list[str], list[dict]]:
    """Validate parameter values, fill missing masses/frequencies and
    derived quantities (Kepler semi-major axis, GW strain, inspiral time).

    If STRICT_ERROR is True, sheet values for parameters in _NUMERIC_PARAMS
    are only used (and thus only feed the mass/frequency/derived-quantity
    calculations below) when they have a valid associated error; see
    _row_has_valid_error().

    If q is tagged as a lower limit, derived quantities are filled as the
    midpoint of the range spanned by q = q_given .. 1, and a range error
    (error_type=None, following the "range" alias convention) is emitted
    for each.

    Returns (field_values_for_BinaryModel, list_of_warnings, derived_errors).
    """
    warnings: list[str] = []
    fields: dict = {}

    for sheet_name, db_field in PARAM_TO_FIELD.items():
        raw = _get_cell(indexed_df, sheet_name)
        if raw is None or _is_blank(raw):
            continue

        if db_field in STRING_FIELDS:
            fields[db_field] = str(raw)[:750]
            continue

        if (STRICT_ERROR and sheet_name in _NUMERIC_PARAMS
                and not _row_has_valid_error(indexed_df, sheet_name)):
            warnings.append(
                f"{sheet_name}={raw}: skipped (STRICT_ERROR is on and this "
                f"value has no valid associated error)"
            )
            continue

        fval = _safe_float(raw)
        if fval is None:
            warnings.append(f"{sheet_name}: could not parse '{raw}' as float")
            continue

        if sheet_name in VALID_RANGES:
            lo, hi = VALID_RANGES[sheet_name]
            if not (lo <= fval <= hi):
                warnings.append(f"{sheet_name}={fval} outside [{lo}, {hi}]")
                continue

        if db_field == "orb_period":
            fval = fval / DAYS_PER_YEAR

        fields[db_field] = fval

    freq_hz_sheet = _safe_float(_get_cell(indexed_df, "orbital frequency (earth frame)"))

    def _derive(base: dict) -> tuple[dict, list[str]]:
        """Fill every derivable quantity from a copy of the parsed fields."""
        f = dict(base)
        notes: list[str] = []

        # Mass value filling
        if f.get("m1") is None or f.get("m2") is None:
            try:
                m1_log, m2_log = calc.find_m1_m2(
                    f.get("m1"), f.get("m2"), f.get("mtot"),
                    f.get("q"), f.get("mc"), f.get("mu"),
                )
                if f.get("m1") is None and m1_log is not None:
                    f["m1"] = m1_log
                    notes.append(f"Filled m1={m1_log:.6g}")
                if f.get("m2") is None and m2_log is not None:
                    f["m2"] = m2_log
                    notes.append(f"Filled m2={m2_log:.6g}")
            except Exception as e:
                notes.append(f"Could not derive m1/m2: {e}")

        m1, m2 = f.get("m1"), f.get("m2")
        if m1 is not None and m2 is not None:
            fill_funcs = [
                ("mtot", calc.Mtot_calc),
                ("mc", calc.Mc_calc),
                ("mu", calc.mu_calc),
                ("q", calc.q_calc),
            ]
            for name, func in fill_funcs:
                if name not in f:
                    try:
                        val = func(m1, m2)
                        if val is not None and not np.isnan(val):
                            f[name] = val
                            notes.append(f"Filled {name}={val:.6g}")
                    except Exception as e:
                        notes.append(f"Failed to compute {name}: {e}")

        # Frequency / period filling
        if f.get("orb_period") is None and freq_hz_sheet is not None:
            try:
                _, T_yr, _ = calc.freq_calc(orbital_frequency_hz=freq_hz_sheet)
                if T_yr is not None and not np.isnan(T_yr):
                    f["orb_period"] = T_yr
                    notes.append(f"Filled orb_period={T_yr:.6g} yr")
            except Exception as e:
                notes.append(f"Frequency filling failed: {e}")

        # Kepler semi-major axis from period + total mass
        if (f.get("semimajor_axis") is None
                and f.get("orb_period") is not None
                and f.get("mtot") is not None):
            try:
                a_pc = calc.kepler_semimajor(f["orb_period"], f["mtot"])
                f["semimajor_axis"] = a_pc
                notes.append(f"Filled semimajor_axis={a_pc:.6g} pc (Kepler)")
            except Exception as e:
                notes.append(f"Kepler semi-major axis failed: {e}")

        # GW strain (needs chirp mass, luminosity distance, GW frequency)
        freq_hz = freq_hz_sheet
        if freq_hz is None and f.get("orb_period"):
            freq_hz = 1.0 / (f["orb_period"] * DAYS_PER_YEAR * 86400)
        if f.get("mc") is not None and lum_dist is not None and freq_hz is not None:
            try:
                f["gw_strain"] = calc.strain_calc(f["mc"], lum_dist, 2 * freq_hz)
                notes.append(f"Filled gw_strain={f['gw_strain']:.6g}")
            except Exception as e:
                notes.append(f"GW strain calc failed: {e}")

        # GW inspiral timescale (years; needs semi-major axis, mtot, mu)
        if (f.get("semimajor_axis") is not None
                and f.get("mtot") is not None
                and f.get("mu") is not None):
            try:
                f["gw_inspiral_timescale"] = calc.tgw_calc(
                    f["semimajor_axis"], f["mtot"], f["mu"]
                )
                notes.append(f"Filled gw_inspiral_timescale={f['gw_inspiral_timescale']:.6g} yr")
            except Exception as e:
                notes.append(f"GW inspiral timescale failed: {e}")

        return f, notes

    # Is q tagged as a lower limit? (Blank Error cells mean parse_errors
    # records nothing for it, so handle the range semantics here.)
    q_etype_raw = _get_cell(indexed_df, "q", "Error type")
    q_is_lower_limit = (
        fields.get("q") is not None
        and not _is_blank(q_etype_raw)
        and str(q_etype_raw).strip().lower() == "lower limit"
    )

    derived_errors: list[dict] = []
    if q_is_lower_limit:
        # Derive everything at both ends of the allowed range q_given..1;
        # store midpoints and a range error for quantities that vary.
        lo_fields, lo_notes = _derive(fields)
        hi_base = dict(fields)
        hi_base["q"] = 1.0
        hi_fields, _ = _derive(hi_base)
        warnings.extend(lo_notes)
        warnings.append(
            f"q={fields['q']:.6g} is a lower limit: derived values filled as "
            f"midpoints of the q={fields['q']:.6g}..1 range"
        )

        merged = dict(lo_fields)
        merged["q"] = fields["q"]  # keep the given lower limit as-is
        for key in ("m1", "m2", "mtot", "mc", "mu",
                    "semimajor_axis", "gw_strain", "gw_inspiral_timescale"):
            lo_v, hi_v = lo_fields.get(key), hi_fields.get(key)
            if key in fields or lo_v is None or hi_v is None:
                continue  # given directly, or not derivable at one endpoint
            span = abs(hi_v - lo_v)
            if span <= 1e-12 * max(abs(hi_v), abs(lo_v)):
                continue  # doesn't actually depend on q
            mid = 0.5 * (lo_v + hi_v)
            merged[key] = mid
            derived_errors.append({
                "property_name": key[:25],
                "error_type": None,  # "range", per _ERROR_TYPE_ALIASES
                "error_lower": min(lo_v, hi_v) - mid,
                "error_upper": max(lo_v, hi_v) - mid,
            })
        fields = merged
    else:
        fields, notes = _derive(fields)
        warnings.extend(notes)

    # Consistency checks (warn only, don't reject). Skipped for
    # lower-limit q: midpoint values are intentionally not mutually
    # consistent, so the check would always fire.
    if (not q_is_lower_limit
            and fields.get("m1") is not None and fields.get("m2") is not None):
        _check_mass_consistency(fields, warnings)

    return fields, warnings, derived_errors


def _check_mass_consistency(fields: dict, warnings: list[str]):
    m1, m2 = fields["m1"], fields["m2"]
    checks = [
        ("mtot", calc.Mtot_calc),
        ("mc", calc.Mc_calc),
        ("mu", calc.mu_calc),
        ("q", calc.q_calc),
    ]
    for name, func in checks:
        given = fields.get(name)
        if given is None:
            continue
        try:
            expected = func(m1, m2)
            if expected and abs(given - expected) > 0.001 * abs(expected):
                warnings.append(f"{name}={given:.6g} inconsistent with m1,m2 (expected {expected:.6g})")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Error parsing
# ---------------------------------------------------------------------------

_ERROR_TYPE_ALIASES = {
    "two sided": "Two-sided",
    "two-sided": "Two-sided",
    "gaussian": "Gaussian",
    "assumed": "Assumed",
    "upper limit": "Upper limit",
    "lower limit": "Lower limit",
    "representative": "Representative",
    "range": None,
}


def parse_errors(indexed_df: pd.DataFrame) -> list[dict]:
    errors = []
    for param in _NUMERIC_PARAMS:
        if not _row_has_valid_error(indexed_df, param):
            continue

        err_raw = _get_cell(indexed_df, param, "Error")
        etype_raw = _get_cell(indexed_df, param, "Error type")
        etype_str = str(etype_raw).strip()
        etype_normalized = _ERROR_TYPE_ALIASES.get(etype_str.lower(), etype_str)

        if not _is_blank(err_raw):
            err_str = str(err_raw).strip()
            if "," in err_str:
                parts = err_str.split(",", 1)
            elif " - " in err_str:
                parts = err_str.split(" - ", 1)
            else:
                parts = [err_str]

            try:
                if len(parts) == 2:
                    error_lower = float(parts[0].strip())
                    error_upper = float(parts[1].strip())
                else:
                    val = abs(float(parts[0].strip()))
                    error_lower = -val
                    error_upper = val
            except ValueError:
                logger.warning("Could not parse error '%s' for %s", err_str, param)
                continue
        else:
            error_lower = 0.0
            error_upper = 0.0

        db_field = PARAM_TO_FIELD.get(param, param)

        # Convert period errors from days to years
        if db_field == "orb_period":
            error_lower /= DAYS_PER_YEAR
            error_upper /= DAYS_PER_YEAR

        errors.append({
            "property_name": db_field[:25],
            "error_type": etype_normalized,
            "error_lower": error_lower,
            "error_upper": error_upper,
        })
    return errors


# ---------------------------------------------------------------------------
# Evidence parsing
# ---------------------------------------------------------------------------

def parse_evidence(indexed_df: pd.DataFrame) -> list[dict]:
    entries = []
    for suffix in ("", "2", "3", "4"):
        cat_key = f"evidence type{suffix}"
        note_key = f"evidence type note{suffix}"
        wb_key = f"evidence type waveband{suffix}"

        cat_val = _get_cell(indexed_df, cat_key)
        if _is_blank(cat_val):
            continue

        category = EVIDENCE_CATEGORY_MAP.get(str(cat_val).strip().lower())
        if category is None:
            logger.warning("Unknown evidence category '%s'", cat_val)
            continue

        note_val = _get_cell(indexed_df, note_key)
        subcat_name = (str(note_val).strip() if not _is_blank(note_val) else str(cat_val).strip()).lower()

        wb_val = _get_cell(indexed_df, wb_key)
        wavebands = []
        if not _is_blank(wb_val):
            for token in str(wb_val).split(";"):
                mapped = WAVEBAND_MAP.get(token.strip().lower())
                if mapped:
                    wavebands.append(mapped)
                elif token.strip():
                    logger.warning("Unknown waveband '%s'", token.strip())

        entries.append({
            "category": category,
            "subcategory_name": subcat_name,
            "wavebands": wavebands,
        })
    return entries


# ---------------------------------------------------------------------------
# NED resolution (optional — failures don't block ingestion)
# ---------------------------------------------------------------------------

NED_MAX_WORKERS = 4
NED_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "ned_cache.json"


def _load_ned_cache() -> dict:
    try:
        if NED_CACHE_PATH.exists():
            return json.loads(NED_CACHE_PATH.read_text())
    except Exception as e:
        logger.warning("Could not load NED disk cache: %s", e)
    return {}


def _save_ned_cache(cache: dict) -> None:
    try:
        NED_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        NED_CACHE_PATH.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        logger.warning("Could not save NED disk cache: %s", e)


def resolve_candidate(ned_name: str) -> dict:
    result = {"jra": 0.0, "jdec": 0.0, "redshift": None, "lum_dist": None}

    try:
        astrodb.clear_ned_cache()
        ra, dec = astrodb.coord_finder(ned_name)
        coords = SkyCoord(ra, dec)
        result["jra"] = float(coords.ra.degree)
        result["jdec"] = float(coords.dec.degree)
    except Exception as e:
        logger.warning("Could not resolve coordinates for %s: %s", ned_name, e)
        return result

    try:
        z, _ = astrodb.redshift(ned_name)
        if z is not None and not np.isnan(z):
            result["redshift"] = z
            dl_mpc, _, _ = calc.cosmo_calc(z)
            result["lum_dist"] = dl_mpc
    except Exception as e:
        logger.warning("Could not get redshift for %s: %s", ned_name, e)

    return result


def resolve_candidates_parallel(names: list[str]) -> dict[str, dict]:
    """Resolve multiple candidates via NED in parallel (I/O-bound).

    Checks the DB and a disk cache before hitting NED, so re-runs only
    query objects that have never been resolved before.
    """
    results: dict[str, dict] = {}

    # 1. Pull already-resolved candidates from the DB.
    for c in Candidate.objects.filter(name__in=names):
        if c.jra is not None and c.redshift is not None:
            results[c.name] = {
                "jra": c.jra,
                "jdec": c.jdec,
                "redshift": c.redshift,
                "lum_dist": c.lum_dist,
            }
            logger.info("Skipping NED for %s — found in DB", c.name)

    # 2. Check disk cache for anything not in the DB.
    disk_cache = _load_ned_cache()
    for name in names:
        if name not in results and name in disk_cache:
            results[name] = disk_cache[name]
            logger.info("Skipping NED for %s — found in disk cache", name)

    # 3. Only hit NED for names not satisfied by DB or cache.
    to_resolve = [n for n in names if n not in results]
    if to_resolve:
        logger.info("Querying NED for %d candidates (%d threads)...", len(to_resolve), NED_MAX_WORKERS)
        with ThreadPoolExecutor(max_workers=NED_MAX_WORKERS) as pool:
            futures = {pool.submit(resolve_candidate, name): name for name in to_resolve}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    ned_result = future.result()
                    results[name] = ned_result
                    disk_cache[name] = ned_result
                except Exception as e:
                    logger.error("NED resolution crashed for %s: %s", name, e)
                    results[name] = {"jra": 0.0, "jdec": 0.0, "redshift": None, "lum_dist": None}
        _save_ned_cache(disk_cache)
    else:
        logger.info("All %d candidates resolved from DB/cache — skipping NED", len(names))

    return results


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def ingest(sheet_key: str = DEFAULT_SHEET_KEY):
    start = time.time()
    now = timezone.now()

    seed_evidence_subcategories()

    stats = {
        "candidates": 0,
        "bibs": 0,
        "models": 0,
        "errors": 0,
        "evidence": 0,
        "skipped": 0,
    }
    all_warnings: list[str] = []

    # ── 1. Fetch and validate master list ──────────────────────────────
    logger.info("Fetching master list from sheet %s", sheet_key)
    model_list = get_model_list(sheet_key)

    required = ["Paper Link", "NED Name", "Model Parameter Details"]
    missing = [c for c in required if c not in model_list.columns]
    if missing:
        raise ValueError(f"Master sheet missing columns: {missing}")

    model_list = model_list.dropna(subset=required)

    # Deduplicate by sheet key
    try:
        model_list["_sheet_key"] = model_list["Model Parameter Details"].apply(_extract_sheet_key)
    except Exception:
        raise ValueError("Could not extract sheet keys from Model Parameter Details URLs")
    before = len(model_list)
    model_list = model_list.drop_duplicates(subset="_sheet_key", keep="first")
    if len(model_list) < before:
        logger.warning("Dropped %d duplicate sheet entries", before - len(model_list))

    # ── 2. Resolve candidates from NED (parallel) ────────────────────
    unique_names = list(model_list["NED Name"].unique())
    logger.info("Resolving %d candidates via NED (%d threads)...", len(unique_names), NED_MAX_WORKERS)
    candidate_cache = resolve_candidates_parallel(unique_names)

    # ── 3. Create or skip Candidate rows ───────────────────────────────
    for name, info in candidate_cache.items():
        _, created = Candidate.objects.get_or_create(
            name=name,
            defaults={
                "jra": info["jra"],
                "jdec": info["jdec"],
                "redshift": info["redshift"],
                "lum_dist": info["lum_dist"],
                "created_at": now,
            },
        )
        if created:
            stats["candidates"] += 1
            logger.info("Created candidate: %s", name)

    # ── 4. Process each parameter sheet ────────────────────────────────
    for _, row in model_list.iterrows():
        ned_name = row["NED Name"]
        paper_link = row["Paper Link"]
        sk = row["_sheet_key"]

        # Skip if already ingested
        if BinaryModel.objects.filter(sheet_id=sk).exists():
            logger.info("Sheet %s already ingested, skipping", sk)
            stats["skipped"] += 1
            continue

        # Fetch parameter sheet
        try:
            param_df = pd.read_csv(
                _csv_url(sk),
                usecols=["Name", "Value", "Error", "Error type"],
                dtype=str,
            )
        except Exception as e:
            msg = f"Failed to fetch sheet {sk} for {ned_name}: {e}"
            logger.error(msg)
            all_warnings.append(msg)
            continue

        indexed = _index_param_sheet(param_df)

        # ── Bib ──
        _, bibcode = extract_bibcode(paper_link)
        logger.info("Source %s: bibcode %s from %s", ned_name, bibcode, paper_link)
        if not bibcode:
            all_warnings.append(f"No bibcode from link: {paper_link}")
            continue
        if len(bibcode) > 29:
            all_warnings.append(f"Bibcode too long ({len(bibcode)} > 29 chars), skipping: {bibcode}")
            continue

        bib_defaults = {"created_at": now, "updated_at": now}
        if bibcode.startswith("10."):  # bib_id is a DOI, record it as such
            bib_defaults["doi"] = bibcode
        bib, created = Bib.objects.get_or_create(
            bib_id=bibcode,
            defaults=bib_defaults,
        )
        if created:
            stats["bibs"] += 1

        # ── Validate & fill parameters (incl. strain / tgw / Kepler) ──
        lum_dist = candidate_cache.get(ned_name, {}).get("lum_dist")
        if lum_dist is None:
            try:
                lum_dist = Candidate.objects.get(name=ned_name).lum_dist
            except Candidate.DoesNotExist:
                pass

        fields, val_warnings, derived_errors = validate_and_fill(indexed, lum_dist=lum_dist)
        all_warnings.extend(val_warnings)

        
        # ── Create BinaryModel ──
        model_kwargs = {k: v for k, v in fields.items() if k in BINARY_MODEL_FIELDS}
        try:
            binary_model = BinaryModel.objects.create(
                candidate_id=ned_name,
                bib_id=bibcode,
                sheet_id=sk,
                created_at=now,
                **model_kwargs,
            )
            stats["models"] += 1
            logger.info("Created BinaryModel %s for %s", binary_model.binary_model_id, ned_name)
        except Exception as e:
            msg = f"BinaryModel creation failed for {ned_name}: {e}"
            logger.error(msg)
            all_warnings.append(msg)
            continue

        # ── Errors (sheet-provided + derived lower-limit ranges) ──
        error_dicts = parse_errors(indexed) + derived_errors
        if error_dicts:
            BinaryModelError.objects.bulk_create(
                [
                    BinaryModelError(
                        binary_model=binary_model,
                        property_name=ed["property_name"],
                        error_type=ed["error_type"],
                        error_upper=ed["error_upper"],
                        error_lower=ed["error_lower"],
                    )
                    for ed in error_dicts
                ],
                ignore_conflicts=True,
            )
            stats["errors"] += len(error_dicts)

        # ── ObsPeriod ──
        period_yr = fields.get("orb_period")
        epoch_mjd = fields.get("orb_period_epoch")
        if period_yr is not None and epoch_mjd is not None:
            obs_period, op_created = ObsPeriod.objects.get_or_create(
                binary_model=binary_model,
                value=period_yr,
                epoch=epoch_mjd,
            )
            if op_created:
                period_err = next(
                    (e for e in error_dicts if e["property_name"] == "orb_period"),
                    None,
                )
                if period_err:
                    ObsPeriodError.objects.get_or_create(
                        obs_period=obs_period,
                        defaults={
                            "error_type": period_err["error_type"],
                            "error_upper": period_err["error_upper"],
                            "error_lower": period_err["error_lower"],
                        },
                    )

        # ── Evidence ──
        for ev in parse_evidence(indexed):
            subcat, _ = EvidenceSubcategory.objects.get_or_create(
                category=ev["category"],
                name=ev["subcategory_name"],
            )
            logger.info("Source %s: evidence subcategory '%s'", ned_name, ev["subcategory_name"])
            model_ev, _ = ModelEvidence.objects.get_or_create(
                binary_model=binary_model,
                subcategory=subcat,
            )
            for wb in ev["wavebands"]:
                ModelEvidenceWaveband.objects.get_or_create(
                    evidence=model_ev,
                    waveband=wb,
                )
            stats["evidence"] += 1

    # ── Summary ────────────────────────────────────────────────────────
    elapsed = time.time() - start
    summary = (
        f"\n{'='*40}\n"
        f"INGESTION SUMMARY\n"
        f"{'='*40}\n"
        f"Candidates created: {stats['candidates']}\n"
        f"Bibs created:       {stats['bibs']}\n"
        f"Models created:     {stats['models']}\n"
        f"Models skipped:     {stats['skipped']}\n"
        f"Errors recorded:    {stats['errors']}\n"
        f"Evidence entries:   {stats['evidence']}\n"
        f"Warnings:           {len(all_warnings)}\n"
        f"Elapsed:            {elapsed:.1f}s\n"
        f"{'='*40}"
    )
    logger.info(summary)
    print(summary)

    if all_warnings:
        print(f"\n{'='*40}\nWARNINGS\n{'='*40}")
        for w in all_warnings:
            print(f"  - {w}")

    return stats
