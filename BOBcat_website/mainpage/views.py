import os
import re
from collections import defaultdict

from django.db import connections
from django.db.utils import DatabaseError
from django.http import JsonResponse
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
    {"key": "redshift",            "label": "Redshift",            "default": False},
    {"key": "lum_dist",            "label": "Luminosity Distance", "default": False},
    {"key": "bib_id",              "label": "Bibcode",             "default": True},
    {"key": "bib_title",           "label": "Paper Title",         "default": False},
    {"key": "bib_year",            "label": "Year",                "default": False},
    {"key": "evidence",            "label": "Evidence",            "default": True},
    {"key": "m1",                  "label": "m1",                  "default": True},
    {"key": "m2",                  "label": "m2",                  "default": True},
    {"key": "mtot",                "label": "Total Mass",          "default": False},
    {"key": "mc",                  "label": "Chirp Mass",          "default": False},
    {"key": "mu",                  "label": "Reduced Mass",        "default": False},
    {"key": "q",                   "label": "Mass Ratio (q)",      "default": True},
    {"key": "eccentricity",        "label": "Eccentricity",        "default": True},
    {"key": "inclination",         "label": "Inclination",         "default": False},
    {"key": "semimajor_axis",      "label": "Semimajor Axis",      "default": False},
    {"key": "separation",          "label": "Separation",          "default": False},
    {"key": "rm_orb_period",       "label": "Orbital Period",      "default": False},
    {"key": "rm_orb_period_epoch", "label": "Period Epoch",        "default": False},
    {"key": "gw_strain",           "label": "GW Strain",           "default": True},
    {"key": "gw_inspiral_timescale", "label": "Inspiral Timescale", "default": False},
    {"key": "summary",             "label": "Summary",             "default": False},
    {"key": "caveats",             "label": "Caveats",             "default": False},
    {"key": "ext_proj",            "label": "External Project",    "default": False},
]

FLOAT_FIELDS = [
    "eccentricity",
    "m1",
    "m2",
    "mtot",
    "mc",
    "mu",
    "q",
    "inclination",
    "semimajor_axis",
    "separation",
    "rm_orb_period",
    "rm_orb_period_epoch",
    "gw_strain",
    "gw_inspiral_timescale",
]

TEXT_FIELDS = [
    "summary",
    "caveats",
    "ext_proj",
]

FLOAT_FIELD_LABELS = {
    "eccentricity":        "Eccentricity",
    "m1":                  "Primary Mass",
    "m2":                  "Secondary Mass",
    "mtot":                "Total Mass",
    "mc":                  "Chirp Mass",
    "mu":                  "Reduced Mass",
    "q":                   "Mass Ratio",
    "inclination":         "Inclination",
    "semimajor_axis":      "Semimajor Axis",
    "separation":          "Separation",
    "rm_orb_period":       "Orbital Period",
    "rm_orb_period_epoch": "Period Epoch",
    "gw_strain":           "GW Strain",
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


def sourcepage(request, name):
    candidate = Candidate.objects.filter(name=name)
    return render(request, "mainpage/sourcepage.html", {"source_data": candidate})


def _form_field_context():
    """Static context needed to render the form panel in either query mode."""
    return {
        "float_fields": [
            {
                "name": field,
                "label": FLOAT_FIELD_LABELS[field],
                "help_text": BinaryModel._meta.get_field(field).help_text or "",
            }
            for field in FLOAT_FIELDS
        ],
        "text_fields": [
            {
                "name": field,
                "label": TEXT_FIELD_LABELS[field],
                "help_text": BinaryModel._meta.get_field(field).help_text or "",
            }
            for field in TEXT_FIELDS
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

    has_query = any(v for k, v in request.GET.items() if k not in ("cols", "download"))

    if request.GET.get("download") == "json":
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
                "rm_orb_period": model.rm_orb_period,
                "rm_orb_period_epoch": model.rm_orb_period_epoch,
                "gw_strain": model.gw_strain,
                "gw_inspiral_timescale": model.gw_inspiral_timescale,
                "summary": model.summary,
                "caveats": model.caveats,
                "ext_proj": model.ext_proj,
            }
            for model in results
        ]
        response = JsonResponse(data, safe=False, json_dumps_params={"indent": 2})
        response["Content-Disposition"] = 'attachment; filename="binary_model_query.json"'
        return response

    default_keys = [col["key"] for col in ALL_COLUMNS if col["default"]]
    selected_keys = request.GET.getlist("cols")
    active_keys = selected_keys if selected_keys else default_keys
    active_key_set = set(active_keys)
    active_columns = [col for col in ALL_COLUMNS if col["key"] in active_key_set]

    result_list = list(results)

    evidence_col_active = "evidence" in active_key_set
    evidence_map: dict[int, list[dict]] = defaultdict(list)
    if evidence_col_active:
        model_ids = [m.binary_model_id for m in result_list]
        for ev in ModelEvidence.objects.filter(
            binary_model_id__in=model_ids,
        ).select_related("subcategory").values(
            "binary_model_id", "subcategory__category",
        ):
            cat = ev["subcategory__category"]
            if cat:
                evidence_map[ev["binary_model_id"]].append({
                    "path": _CATEGORY_TILES.get(cat, _DEFAULT_TILE),
                    "label": _CATEGORY_LABELS.get(cat, cat),
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
            elif key in _FK_ACCESSORS:
                val = _FK_ACCESSORS[key](model)
                row.append({"is_evidence": False, "value": val if val is not None and val != "" else "-"})
            else:
                val = getattr(model, key, None)
                row.append({"is_evidence": False, "value": val if val is not None and val != "" else "-"})
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
    }
    return render(request, "mainpage/binary_model_search.html", context)
