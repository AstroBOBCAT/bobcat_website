import csv
import io
import os
import re
from collections import defaultdict
from urllib.parse import urlencode

from django.db import connections
from django.db.models.expressions import RawSQL
from django.db.utils import DatabaseError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from .models import BinaryModel, Candidate, Bib, ModelEvidence, EvidenceSubcategory, EvidenceCategory
from . import adql as _adql

_MAX_SQL_ROWS = 1000
_FORBIDDEN_SQL = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC(?:UTE)?|GRANT|REVOKE|COPY|VACUUM)\b',
    re.IGNORECASE,
)


_NOT_CONFIGURED_ERROR = (
    "Queries are unavailable: the read-only database user is not configured.\n"
    "Run `python manage.py setup_readonly_db_user` then set "
    "READONLY_DB_USER and READONLY_DB_PASSWORD in your .db_info file and restart."
)


def _execute_validated(sql: str):
    """Validate and execute a plain SQL string via the readonly connection."""
    if not os.environ.get("READONLY_DB_PASSWORD"):
        return None, None, _NOT_CONFIGURED_ERROR
    if not re.match(r'\s*SELECT\b', sql, re.IGNORECASE):
        return None, None, "Only SELECT statements are permitted."
    if _FORBIDDEN_SQL.search(sql):
        return None, None, "Query contains a forbidden keyword."
    if ";" in sql:
        return None, None, "Multiple statements (semicolons) are not permitted."
    try:
        with connections["readonly"].cursor() as cursor:
            cursor.execute(sql)
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchmany(_MAX_SQL_ROWS)
        return columns, rows, None
    except DatabaseError as exc:
        return None, None, str(exc)


def _run_sql_query(query: str):
    """Execute a plain SQL query with no ADQL translation."""
    return _execute_validated(query)


def _run_adql_query(query: str):
    """Translate ADQL to SQL then execute."""
    translated, error = _adql.translate(query)
    if error:
        return None, None, error
    return _execute_validated(translated)

_CATEGORY_TILES = {
    'spectral_line_variability':            "mainpage/tiles/tile_variable_spectral_line.png",
    'spectral_line_snapshot':               "mainpage/tiles/tile_spectral_line_snapshot.png",
    'continuum_variability':                "mainpage/tiles/tile_continuum_variability.png",
    'spatially_resolved_offset_or_dual_AGN': "mainpage/tiles/tile_resolved_pair_offset.png",
    'pc_jet_morphology':                    "mainpage/tiles/tile_pc_jet_morphology.png",
    'kpc_jet_morphology':                   "mainpage/tiles/tile_kpc_jet_morphology.png",
    'host_galaxy':                          "mainpage/tiles/tile_host_galaxy.png",
    'gravitational_wave':                   "mainpage/tiles/tile_gravitational_waves.png",
    'SED_feature':                          "mainpage/tiles/tile_spectral_continuum.png",
}
_CATEGORY_LABELS = dict(EvidenceCategory.choices)
_DEFAULT_TILE = "mainpage/tiles/tile_spectral_continuum.png"


ALL_COLUMNS = [
    {"key": "candidate_name",      "label": "Candidate",           "default": True},
    {"key": "jra",                 "label": "RA (J2000)",          "default": True},
    {"key": "jdec",                "label": "Dec (J2000)",         "default": True},
    {"key": "redshift",            "label": "Redshift",            "default": True},
    {"key": "lum_dist",            "label": "Luminosity Distance", "default": False},
    {"key": "bib_id",              "label": "Model Bibcode",             "default": True},
    {"key": "bib_title",           "label": "Paper Title",         "default": False},
    {"key": "bib_year",            "label": "Year",                "default": False},
    {"key": "evidence",            "label": "Evidence",            "default": True},
    {"key": "m1",                  "label": "log(m1)",                  "default": True},
    {"key": "m2",                  "label": "log(m2)",                  "default": True},
    {"key": "mtot",                "label": "log(Total Mass)",          "default": False},
    {"key": "mc",                  "label": "log(Chirp Mass)",          "default": False},
    {"key": "mu",                  "label": "log(Reduced Mass)",        "default": False},
    {"key": "q",                   "label": "Mass Ratio (q)",      "default": True},
    {"key": "eccentricity",        "label": "Eccentricity",        "default": True},
    {"key": "inclination",         "label": "Inclination",         "default": False},
    {"key": "semimajor_axis",      "label": "Semimajor Axis",      "default": False},
    {"key": "separation",          "label": "Separation",          "default": False},
    {"key": "orb_period",       "label": "Orbital Period",      "default": False},
    {"key": "orb_period_epoch", "label": "Period Epoch",        "default": False},
    {"key": "gw_strain",           "label": "GW Strain",           "default": True},
    {"key": "gw_inspiral_timescale", "label": "Inspiral Timescale", "default": False},
    {"key": "summary",             "label": "Summary",             "default": False},
    {"key": "caveats",             "label": "Caveats",             "default": False},
    {"key": "ext_proj",            "label": "External Project",    "default": False},
]

CANDIDATE_FLOAT_FIELDS = ["jra", "jdec", "redshift"]
MASS_FIELDS   = ["m1", "m2", "mtot", "mc", "mu", "q"]
ORBIT_FIELDS  = ["eccentricity", "inclination", "semimajor_axis", "separation", "orb_period", "orb_period_epoch"]
GW_FIELDS     = ["gw_strain", "gw_inspiral_timescale"]

FLOAT_FIELDS = MASS_FIELDS + ORBIT_FIELDS + GW_FIELDS

TEXT_FIELDS = [
    "summary",
    "caveats",
    "ext_proj",
]

FLOAT_FIELD_LABELS = {
    "jra":                   "RA (J2000)",
    "jdec":                  "Dec (J2000)",
    "redshift":              "Redshift",
    "eccentricity":          "Eccentricity",
    "m1":                    "Primary Mass",
    "m2":                    "Secondary Mass",
    "mtot":                  "Total Mass",
    "mc":                    "Chirp Mass",
    "mu":                    "Reduced Mass",
    "q":                     "Mass Ratio",
    "inclination":           "Inclination",
    "semimajor_axis":        "Semimajor Axis",
    "separation":            "Separation",
    "orb_period":         "Orbital Period",
    "orb_period_epoch":   "Period Epoch",
    "gw_strain":             "GW Strain",
    "gw_inspiral_timescale": "Inspiral Timescale",
}

TEXT_FIELD_LABELS = {
    "summary":  "Summary",
    "caveats":  "Caveats",
    "ext_proj": "External Project",
}

_FK_ACCESSORS = {
    "candidate_name": lambda m: m.candidate.name,
    "jra":            lambda m: m.candidate.jra,
    "jdec":           lambda m: m.candidate.jdec,
    "redshift":       lambda m: m.candidate.redshift,
    "lum_dist":       lambda m: m.candidate.lum_dist,
    "bib_id":         lambda m: m.bib.bib_id,
    "bib_title":      lambda m: m.bib.title,
    "bib_year":       lambda m: m.bib.year,
}

_SORT_ORM_FIELDS = {
    "candidate_name": "candidate__name",
    "jra":            "candidate__jra",
    "jdec":           "candidate__jdec",
    "redshift":       "candidate__redshift",
    "lum_dist":       "candidate__lum_dist",
    "bib_id":         "bib__bib_id",
    "bib_title":      "bib__title",
    "bib_year":       "bib__year",
}
_SORTABLE_KEYS = {col["key"] for col in ALL_COLUMNS if col["key"] != "evidence"}

# Table display controls
_DISPLAY_FORMATS = {
    "jra":        "{:.5f}",   # RA (J2000), degrees
    "jdec":       "{:.5f}",   # Dec (J2000), degrees
    "redshift":   "{:.4f}",
    "lum_dist":   "{:.1f}",
    "mtot":       "{:.2f}",   # total mass — scientific notation
    "m1":         "{:.2f}",
    "m2":         "{:.2f}",
    "mc":         "{:.2f}",
    "mu":         "{:.2f}",
    "q":          "{:.4f}",
    "eccentricity": "{:.2f}",
    "gw_strain":  "{:.4f}",
    # add more keys as needed
}

def sourcepage(request, name):
    candidate = Candidate.objects.filter(name=name)
    return render(request, "mainpage/sourcepage.html", {"source_data": candidate})

def _format_for_display(key, val):
    """Format a cell value for HTML display. Returns '-' for empty/null."""
    if val is None or val == "":
        return "-"
    fmt = _DISPLAY_FORMATS.get(key)
    if fmt is None:
        return val
    try:
        return fmt.format(float(val))
    except (TypeError, ValueError):
        return val

def _form_field_context():
    """Static context needed to render the form panel in either query mode."""

    def _bm_fields(names):
        return [
            {"name": f, "label": FLOAT_FIELD_LABELS[f], "help_text": BinaryModel._meta.get_field(f).help_text or ""}
            for f in names
        ]

    return {
        "candidate_float_fields": [
            {"name": f, "label": FLOAT_FIELD_LABELS[f], "help_text": Candidate._meta.get_field(f).help_text or ""}
            for f in CANDIDATE_FLOAT_FIELDS
        ],
        "mass_fields":  _bm_fields(MASS_FIELDS),
        "orbit_fields": _bm_fields(ORBIT_FIELDS),
        "gw_fields":    _bm_fields(GW_FIELDS),
        "evidence_categories": [
            {"value": val, "label": label}
            for val, label in EvidenceCategory.choices
        ],
        "text_fields": [
            {"name": f, "label": TEXT_FIELD_LABELS[f], "help_text": BinaryModel._meta.get_field(f).help_text or ""}
            for f in TEXT_FIELDS
        ],
        "all_columns": [
            {**col, "checked": col["default"]}
            for col in ALL_COLUMNS
        ],
    }


def binary_model_search(request):
    if not Candidate.objects.exists():
        context = {
            **_form_field_context(),
            "query_mode": "form",
            "empty_db": True,
            "rows": [],
            "result_count": 0,
            "has_query": False,
            "active_columns": [],
        }
        return render(request, "mainpage/binary_model_search.html", context)

    sql_query  = request.GET.get("sql_query",  "").strip()
    adql_query = request.GET.get("adql_query", "").strip()
    mode       = request.GET.get("mode", "form")

    if sql_query or adql_query or mode in ("sql", "adql"):
        if sql_query:
            cols, sql_rows, error = _run_sql_query(sql_query)
            query_mode, active_q  = "sql",  sql_query
        elif adql_query:
            cols, sql_rows, error = _run_adql_query(adql_query)
            query_mode, active_q  = "adql", adql_query
        else:
            cols, sql_rows, error = [], [], None
            query_mode, active_q  = mode, ""

        context = {
            **_form_field_context(),
            "query_mode":  query_mode,
            "sql_query":   sql_query,
            "adql_query":  adql_query,
            "sql_columns": cols or [],
            "sql_rows":    sql_rows or [],
            "sql_error":   error,
            "result_count": len(sql_rows) if sql_rows else 0,
            "has_query":   bool(sql_query or adql_query),
            "active_columns": [],
            "rows": [],
        }
        return render(request, "mainpage/binary_model_search.html", context)

    results = BinaryModel.objects.select_related("candidate", "bib").all()

    for field in TEXT_FIELDS:
        value = request.GET.get(field)
        if value:
            results = results.filter(**{f"{field}__icontains": value})

    for field in FLOAT_FIELDS:
        exact_value = request.GET.get(field)
        min_value = request.GET.get(f"{field}_min")
        max_value = request.GET.get(f"{field}_max")

        if exact_value:
            try:
                results = results.filter(**{field: float(exact_value)})
            except ValueError:
                pass

        if min_value:
            try:
                results = results.filter(**{f"{field}__gte": float(min_value)})
            except ValueError:
                pass

        if max_value:
            try:
                results = results.filter(**{f"{field}__lte": float(max_value)})
            except ValueError:
                pass

    candidate_name = request.GET.get("candidate_name")
    if candidate_name:
        results = results.filter(candidate__name__icontains=candidate_name)

    bib_id = request.GET.get("bib_id")
    if bib_id:
        results = results.filter(bib__bib_id__icontains=bib_id)

    for field in CANDIDATE_FLOAT_FIELDS:
        orm_prefix = f"candidate__{field}"
        exact_value = request.GET.get(field)
        min_value = request.GET.get(f"{field}_min")
        max_value = request.GET.get(f"{field}_max")
        if exact_value:
            try:
                results = results.filter(**{orm_prefix: float(exact_value)})
            except ValueError:
                pass
        if min_value:
            try:
                results = results.filter(**{f"{orm_prefix}__gte": float(min_value)})
            except ValueError:
                pass
        if max_value:
            try:
                results = results.filter(**{f"{orm_prefix}__lte": float(max_value)})
            except ValueError:
                pass

    cone_ra = request.GET.get("cone_ra", "").strip()
    cone_dec = request.GET.get("cone_dec", "").strip()
    cone_radius = request.GET.get("cone_radius", "").strip()
    cone_error = ""
    if cone_ra and cone_dec and cone_radius:
        try:
            ra_val = float(cone_ra)
            dec_val = float(cone_dec)
            r_val = float(cone_radius)
            if not (0 <= ra_val <= 360):
                cone_error = "RA must be between 0 and 360 degrees."
            elif not (-90 <= dec_val <= 90):
                cone_error = "Dec must be between −90 and +90 degrees."
            elif not (0 < r_val <= 180):
                cone_error = "Radius must be between 0 and 180 degrees."
            else:
                results = results.extra(
                    where=[
                        "scircle(spoint(radians(%s), radians(%s)), radians(%s)) @> "
                        'spoint(radians(candidate.jra), radians(candidate.jdec))'
                    ],
                    params=[ra_val, dec_val, r_val],
                )
        except ValueError:
            cone_error = "RA, Dec, and Radius must be numeric values."
    elif cone_ra or cone_dec or cone_radius:
        cone_error = "Cone search requires all three fields: RA, Dec, and Radius."

    ev_cats = request.GET.getlist("ev_cat")
    if ev_cats:
        results = results.filter(
            modelevidence__subcategory__category__in=ev_cats,
        ).distinct()

    ev_subcat = request.GET.get("ev_subcat", "").strip()
    if ev_subcat:
        results = results.filter(
            modelevidence__subcategory__name__icontains=ev_subcat,
        ).distinct()

    sort_key = request.GET.get("sort", "")
    sort_dir = request.GET.get("sort_dir", "asc")
    if sort_key in _SORTABLE_KEYS:
        orm_field = _SORT_ORM_FIELDS.get(sort_key, sort_key)
        if sort_dir == "desc":
            orm_field = f"-{orm_field}"
        results = results.order_by(orm_field)

    has_query = any(v for k, v in request.GET.items() if k not in ("cols", "download", "sort", "sort_dir"))

    download_fmt = request.GET.get("download")
    if download_fmt in ("json", "csv"):
        data = [
            {
                "candidate_name": model.candidate.name,
                "jra": model.candidate.jra,
                "jdec": model.candidate.jdec,
                "redshift": model.candidate.redshift,
                "lum_dist": model.candidate.lum_dist,
                "bib_id": model.bib.bib_id,
                "bib_title": model.bib.title,
                "bib_year": model.bib.year,
                "eccentricity": model.eccentricity,
                "m1": model.m1,
                "m2": model.m2,
                "mtot": model.mtot,
                "mc": model.mc,
                "mu": model.mu,
                "q": model.q,
                "inclination": model.inclination,
                "semimajor_axis": model.semimajor_axis,
                "separation": model.separation,
                "orb_period": model.orb_period,
                "orb_period_epoch": model.orb_period_epoch,
                "gw_strain": model.gw_strain,
                "gw_inspiral_timescale": model.gw_inspiral_timescale,
                "summary": model.summary,
                "caveats": model.caveats,
                "ext_proj": model.ext_proj,
            }
            for model in results
        ]

        if download_fmt == "csv":
            buf = io.StringIO()
            if data:
                writer = csv.DictWriter(buf, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            response = HttpResponse(buf.getvalue(), content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="binary_model_query.csv"'
            return response

        response = JsonResponse(data, safe=False, json_dumps_params={"indent": 2})
        response["Content-Disposition"] = 'attachment; filename="binary_model_query.json"'
        return response

    default_keys = [col["key"] for col in ALL_COLUMNS if col["default"]]
    selected_keys = request.GET.getlist("cols")
    active_keys = selected_keys if selected_keys else default_keys
    active_key_set = set(active_keys)
    active_columns = [{**col} for col in ALL_COLUMNS if col["key"] in active_key_set]

    base_params = [
        (k, v)
        for k, vs in request.GET.lists()
        for v in vs
        if k not in ("sort", "sort_dir")
    ]
    for col in active_columns:
        key = col["key"]
        if key not in _SORTABLE_KEYS:
            col["sortable"] = False
            continue
        col["sortable"] = True
        if key == sort_key:
            new_dir = "desc" if sort_dir == "asc" else "asc"
            col["sort_indicator"] = "▲" if sort_dir == "asc" else "▼"
        else:
            new_dir = "asc"
            col["sort_indicator"] = ""
        col["sort_url"] = "?" + urlencode(base_params + [("sort", key), ("sort_dir", new_dir)])

    result_list = list(results)

    evidence_col_active = "evidence" in active_key_set
    evidence_map: dict[int, list[dict]] = defaultdict(list)
    if evidence_col_active:
        model_ids = [m.binary_model_id for m in result_list]
        # Collect subcategory names grouped by (model, category)
        _ev_by_model_cat: dict[tuple[int, str], list[str]] = defaultdict(list)
        for ev in ModelEvidence.objects.filter(
            binary_model_id__in=model_ids,
        ).select_related("subcategory").values(
            "binary_model_id", "subcategory__category", "subcategory__name",
        ):
            cat = ev["subcategory__category"]
            if cat:
                subcat = ev.get("subcategory__name", "")
                _ev_by_model_cat[(ev["binary_model_id"], cat)].append(subcat)
        for (mid, cat), subcats in _ev_by_model_cat.items():
            cat_label = _CATEGORY_LABELS.get(cat, cat)
            tile_path = _CATEGORY_TILES.get(cat, _DEFAULT_TILE)
            for sc in subcats:
                evidence_map[mid].append({
                    "path": tile_path,
                    "label": f"{cat_label}: {sc}" if sc else cat_label,
                })

    rows = []
    for model in result_list:
        row = []
        for col in active_columns:
            key = col["key"]
            if key == "evidence":
                row.append({
                    "is_evidence": True,
                    "tiles": evidence_map.get(model.binary_model_id, []),
                })
            elif key == "bib_id":
                bib = model.bib
                val = bib.bib_id or "-"
                if bib.doi:
                    url = f"https://doi.org/{bib.doi}"
                elif bib.bib_id:
                    url = f"https://ui.adsabs.harvard.edu/abs/{bib.bib_id}"
                else:
                    url = ""
                row.append({"is_evidence": False, "value": val, "link": url})
            elif key in _FK_ACCESSORS:
                val = _FK_ACCESSORS[key](model)
                row.append({"is_evidence": False, "value": _format_for_display(key, val)})
            else:
                val = getattr(model, key, None)
                row.append({"is_evidence": False, "value": _format_for_display(key, val)})
        rows.append(row)

    form_ctx = _form_field_context()
    form_ctx["all_columns"] = [
        {**col, "checked": col["key"] in active_key_set}
        for col in ALL_COLUMNS
    ]
    context = {
        **form_ctx,
        "query_mode": "form",
        "rows": rows,
        "result_count": len(rows),
        "has_query": has_query,
        "active_columns": active_columns,
        "cone_error": cone_error,
    }
    return render(request, "mainpage/binary_model_search.html", context)
