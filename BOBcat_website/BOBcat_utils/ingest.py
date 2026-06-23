import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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

DEFAULT_SHEET_KEY = "1DTFQ3KMg1qkonvCv6veT0TqLmC4hbdjUQ09_CQfVMoI"

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
    "period epoch": "rm_orb_period_epoch",
    "orbital period (earth frame)": "rm_orb_period",
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
    """Return (scix_link, bibcode) from an ADS or SciX URL."""
    link = str(link).strip()
    for domain in ("ui.adsabs", "scixplorer.org"):
        if domain in link:
            parts = link.rstrip("/").split("/")
            bibcode = parts[-1] if parts[-1] != "abstract" else parts[-2]
            bibcode = bibcode.replace("%26", "&") # Fixes A%26A URL code for A&A journal (and potentially others)
            scix_link = f"https://scixplorer.org/abs/{bibcode}"
            return scix_link, bibcode
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

def validate_and_fill(indexed_df: pd.DataFrame) -> tuple[dict, list[str]]:
    """Validate parameter values, fill missing masses/frequencies.

    Returns (field_values_for_BinaryModel, list_of_warnings).
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

        fval = _safe_float(raw)
        if fval is None:
            warnings.append(f"{sheet_name}: could not parse '{raw}' as float")
            continue

        if sheet_name in VALID_RANGES:
            lo, hi = VALID_RANGES[sheet_name]
            if not (lo <= fval <= hi):
                warnings.append(f"{sheet_name}={fval} outside [{lo}, {hi}]")
                continue

        if db_field == "rm_orb_period":
            fval = fval / DAYS_PER_YEAR

        fields[db_field] = fval

    # Mass value filling via calc.update_masses
    m1 = fields.get("m1")
    m2 = fields.get("m2")
    mtot = fields.get("mtot")
    mc = fields.get("mc")
    mu = fields.get("mu")
    q = fields.get("q")

    try:
        mass_array, updated = calc.update_masses(m1, m2, mtot, mc, mu, q)
        mass_fields = ["m1", "m2", "mtot", "mc", "mu", "q"]
        for i, mf in enumerate(mass_fields):
            if mf not in fields and mass_array[i] is not None and not np.isnan(mass_array[i]):
                fields[mf] = mass_array[i]
                warnings.append(f"Filled {mf}={mass_array[i]:.6g}")
    except Exception as e:
        warnings.append(f"Mass filling failed: {e}")

    # Frequency / period filling
    period_days = _safe_float(_get_cell(indexed_df, "orbital period (earth frame)"))
    freq_hz = _safe_float(_get_cell(indexed_df, "orbital frequency (earth frame)"))

    if period_days is not None or freq_hz is not None:
        try:
            period_yr = period_days / DAYS_PER_YEAR if period_days is not None else None
            f_orb, T_yr, _ = calc.freq_calc(T=period_yr, f_orb=freq_hz)
            if "rm_orb_period" not in fields and T_yr is not None and not np.isnan(T_yr):
                fields["rm_orb_period"] = T_yr
                warnings.append(f"Filled rm_orb_period={T_yr:.6g} yr")
        except Exception as e:
            warnings.append(f"Frequency filling failed: {e}")

    # Consistency checks (warn only, don't reject)
    if fields.get("m1") is not None and fields.get("m2") is not None:
        _check_mass_consistency(fields, warnings)

    return fields, warnings


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

_NUMERIC_PARAMS = [
    "eccentricity", "log(m1)", "log(m2)", "log(total mass)",
    "log(chirp mass)", "log(reduced mass)", "q", "inclination",
    "semi-major axis", "separation", "orbital period (earth frame)",
]

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
        err_raw = _get_cell(indexed_df, param, "Error")
        etype_raw = _get_cell(indexed_df, param, "Error type")
        if _is_blank(err_raw) or _is_blank(etype_raw):
            continue

        etype_str = str(etype_raw).strip()
        etype_normalized = _ERROR_TYPE_ALIASES.get(etype_str.lower(), etype_str)
        if etype_normalized is not None and etype_normalized not in VALID_ERROR_TYPES:
            logger.warning("Unknown error type '%s' for %s, skipping", etype_str, param)
            continue

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

        db_field = PARAM_TO_FIELD.get(param, param)

        # Convert period errors from days to years
        if db_field == "rm_orb_period":
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


def resolve_candidate(ned_name: str) -> dict:
    result = {"jra": 0.0, "jdec": 0.0, "redshift": None, "lum_dist": None}

    try:
        #astrodb.clear_ned_cache() # This was bugged on my machine (Jordan)
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
    """Resolve multiple candidates via NED in parallel (I/O-bound)."""
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=NED_MAX_WORKERS) as pool:
        futures = {pool.submit(resolve_candidate, name): name for name in names}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                logger.error("NED resolution crashed for %s: %s", name, e)
                results[name] = {"jra": 0.0, "jdec": 0.0, "redshift": None, "lum_dist": None}
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
    print("DEBUG: RESOLVING CANDIDATES")
    unique_names = list(model_list["NED Name"].unique())
    logger.info("Resolving %d candidates via NED (%d threads)...", len(unique_names), NED_MAX_WORKERS)
    candidate_cache = resolve_candidates_parallel(unique_names)

    # ── 3. Create or skip Candidate rows ───────────────────────────────
    print("DEBUG: CREATE OR SKIP CANDIDATES")
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
    print("DEBUG: PROCESS PARAM SHEETS")
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

        print("DEBUG: GOT A PARAM SHEET")
        # ── Bib ──
        _, bibcode = extract_bibcode(paper_link)
        print(f"DEBUG: SOURCE {ned_name} FOUND BIBCODE {bibcode} for {paper_link}")
        if not bibcode:
            all_warnings.append(f"No bibcode from link: {paper_link}")
            continue
        if len(bibcode) > 25:
            all_warnings.append(f"Bibcode too long ({len(bibcode)} chars), skipping: {bibcode}")
            continue

        bib, created = Bib.objects.get_or_create(
            bib_id=bibcode,
            defaults={"created_at": now, "updated_at": now},
        )
        if created:
            stats["bibs"] += 1

        # ── Validate & fill parameters ──
        fields, val_warnings = validate_and_fill(indexed)
        all_warnings.extend(val_warnings)

        # ── GW strain ──
        gw_strain = None
        mc_log = fields.get("mc")
        lum_dist = candidate_cache.get(ned_name, {}).get("lum_dist")
        freq_hz = _safe_float(_get_cell(indexed, "orbital frequency (earth frame)"))

        if mc_log is not None and lum_dist is not None and freq_hz is not None:
            try:
                gw_strain = calc.strain_calc(10**mc_log, lum_dist, 2 * freq_hz)
                print(gw_strain)
            except Exception as e:
                all_warnings.append(f"GW strain calc failed for {ned_name}: {e}")
        else:
            print("Strain calculation values reading as none")

        # ── Create BinaryModel ──
        model_kwargs = {k: v for k, v in fields.items() if k in BINARY_MODEL_FIELDS}
        try:
            binary_model = BinaryModel.objects.create(
                candidate_id=ned_name,
                bib_id=bibcode,
                sheet_id=sk,
                created_at=now,
                gw_strain=gw_strain,
                **model_kwargs,
            )
            stats["models"] += 1
            logger.info("Created BinaryModel %s for %s", binary_model.binary_model_id, ned_name)
        except Exception as e:
            msg = f"BinaryModel creation failed for {ned_name}: {e}"
            logger.error(msg)
            all_warnings.append(msg)
            continue

        # ── Errors ──
        error_dicts = parse_errors(indexed)
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
        period_yr = fields.get("rm_orb_period")
        epoch_mjd = fields.get("rm_orb_period_epoch")
        if period_yr is not None and epoch_mjd is not None:
            obs_period, op_created = ObsPeriod.objects.get_or_create(
                binary_model=binary_model,
                value=period_yr,
                epoch=epoch_mjd,
            )
            if op_created:
                period_err = next(
                    (e for e in error_dicts if e["property_name"] == "rm_orb_period"),
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
            print(f"for source {ned_name} found subcategory {ev["subcategory_name"]}")
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
