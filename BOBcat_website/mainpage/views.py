import os
import re
from collections import defaultdict

from django.db import connections
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render

from .models import BinaryModel, Evidence, Papers
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

#A simple prototype for the frontend. Don't worry about this structure its not representative of the final product.
#Also if you want to replace this entire thing thats fine.

_TILE_IMAGES = [
    "mainpage/tiles/tile_continuum_variability.png",
    "mainpage/tiles/tile_gravitational_waves.png",
    "mainpage/tiles/tile_host_galaxy.png",
    "mainpage/tiles/tile_kpc_jet_morphology.png",
    "mainpage/tiles/tile_pc_jet_morphology.png",
    "mainpage/tiles/tile_resolved_pair_offset.png",
    "mainpage/tiles/tile_spectral_continuum.png",
    "mainpage/tiles/tile_spectral_line_snapshot.png",
    "mainpage/tiles/tile_variable_spectral_line.png",
]

def _evidence_tile_path(type_str: str) -> str:
    """Pick a tile image for an evidence type.

    Uses a stable hash of the type string so the same type always maps to
    the same tile, regardless of naming conventions in the data.
    """
    return _TILE_IMAGES[hash(type_str) % len(_TILE_IMAGES)]


ALL_COLUMNS = [
    {"key": "candidate_name", "label": "Candidate",          "default": True},
    {"key": "ned_name",       "label": "NED Name",           "default": True},
    {"key": "paper",          "label": "Paper",              "default": True},
    {"key": "evidence",       "label": "Evidence",           "default": True},
    {"key": "sheet_id",       "label": "Sheet ID",           "default": False},#TODO remove
    {"key": "m1",             "label": "m1",                 "default": True},
    {"key": "m2",             "label": "m2",                 "default": True},
    {"key": "mtot",           "label": "Total Mass",         "default": False},
    {"key": "mc",             "label": "Chirp Mass",         "default": False},
    {"key": "mu",             "label": "Reduced Mass",       "default": False},
    {"key": "q",              "label": "Mass Ratio (q)",     "default": True},
    {"key": "eccentricity",   "label": "Eccentricity",       "default": True},
    {"key": "inclination",    "label": "Inclination",        "default": False},
    {"key": "semimajor_axis", "label": "Semimajor Axis",     "default": False},
    {"key": "seperation",     "label": "Separation",         "default": False},
    {"key": "period_epoch",   "label": "Period Epoch",       "default": False},
    {"key": "orb_freq",       "label": "Orbital Frequency",  "default": False},
    {"key": "orb_period",     "label": "Orbital Period",     "default": False},
    {"key": "gw_strain",      "label": "GW Strain",          "default": True},
    {"key": "gw_freq",        "label": "GW Frequency",       "default": True},
    {"key": "gw_strain_err",  "label": "GW Strain Error",    "default": False},
    {"key": "gw_freq_err",    "label": "GW Frequency Error", "default": False},
    {"key": "summary",        "label": "Summary",            "default": False},
    {"key": "caveats",        "label": "Caveats",            "default": False},
    {"key": "ext_proj",       "label": "External Project",   "default": False},
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
    "seperation",
    "period_epoch",
    "orb_freq",
    "orb_period",
    "gw_strain",
    "gw_freq",
    "gw_strain_err",
    "gw_freq_err",
]

#TODO organize fields more.
#TODO: Mass (m1-q), rotation (inclination-orb_period), GW (gw_strain-gw_freq_err),
TEXT_FIELDS = [
    "sheet_id", #TODO remove
    "paper",
    "summary",
    "caveats",
    "ext_proj",
]

FLOAT_FIELD_LABELS = {
    "eccentricity": "Eccentricity",
    "m1": "Primary Mass",
    "m2": "Secondary Mass",
    "mtot": "Total Mass",
    "mc": "Chirp Mass",
    "mu": "Reduced Mass",
    "q": "Mass Ratio",
    "inclination": "Inclination",
    "semimajor_axis": "Semimajor Axis",
    "seperation": "Separation",
    "period_epoch": "Period Epoch",
    "orb_freq": "Orbital Frequency",
    "orb_period": "Orbital Period",
    "gw_strain": "GW Strain",
    "gw_freq": "GW Frequency",
    "gw_strain_err": "GW Strain Error",
    "gw_freq_err": "GW Frequency Error",
}

TEXT_FIELD_LABELS = {
    "sheet_id": "Sheet ID",
    "paper": "Paper",
    "summary": "Summary",
    "caveats": "Caveats",
    "ext_proj": "External Project",
}


def sourcepage(request, name):
    source_search_result_data = Papers.objects.filter(candidate_name=name)
    return render(request, "mainpage/sourcepage.html", {"source_data": source_search_result_data})

def _form_field_context():
    """Static context needed to render the form panel in either query mode."""
    return {
        "float_fields": [
            {
                "name": field,
                "label": FLOAT_FIELD_LABELS[field],
                "help_text": BinaryModel._meta.get_field(field).help_text,
            }
            for field in FLOAT_FIELDS
        ],
        "text_fields": [
            {
                "name": field,
                "label": TEXT_FIELD_LABELS[field],
                "help_text": BinaryModel._meta.get_field(field).help_text,
            }
            for field in TEXT_FIELDS
        ],
        "all_columns": [
            {**col, "checked": col["default"]}
            for col in ALL_COLUMNS
        ],
    }


#The primary method that returns the information in the mainpage.
def binary_model_search(request):
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

    results = BinaryModel.objects.select_related("model_param_link").all()

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
        results = results.filter(model_param_link__candidate_name__icontains=candidate_name)

    ned_name = request.GET.get("ned_name")
    if ned_name:
        results = results.filter(model_param_link__ned_name__icontains=ned_name)

    has_query = any(v for k, v in request.GET.items() if k not in ("cols", "download"))

    if request.GET.get("download") == "json":
        data = [
            {
                "candidate_name": model.model_param_link.candidate_name,
                "ned_name": model.model_param_link.ned_name,
                "paper_link": model.model_param_link.paper_link,
                "model_param_link": model.model_param_link.model_param_link,
                "sheet_id": model.sheet_id,
                "paper": model.paper,
                "eccentricity": model.eccentricity,
                "m1": model.m1,
                "m2": model.m2,
                "mtot": model.mtot,
                "mc": model.mc,
                "mu": model.mu,
                "q": model.q,
                "inclination": model.inclination,
                "semimajor_axis": model.semimajor_axis,
                "seperation": model.seperation,
                "period_epoch": model.period_epoch,
                "orb_freq": model.orb_freq,
                "orb_period": model.orb_period,
                "summary": model.summary,
                "caveats": model.caveats,
                "ext_proj": model.ext_proj,
                "gw_strain": model.gw_strain,
                "gw_freq": model.gw_freq,
                "gw_strain_err": model.gw_strain_err,
                "gw_freq_err": model.gw_freq_err,
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

    # Materialise queryset once so we can reuse the list for evidence lookup
    result_list = list(results)

    # Build evidence map in a single DB query (avoids N+1)
    evidence_col_active = "evidence" in active_key_set
    evidence_map: dict[str, list[dict]] = defaultdict(list)
    if evidence_col_active:
        paper_ids = [m.model_param_link_id for m in result_list]
        for ev in Evidence.objects.filter(
            model_param_link_id__in=paper_ids
        ).values("model_param_link_id", "type"):
            if ev["type"]:
                evidence_map[ev["model_param_link_id"]].append({
                    "path": _evidence_tile_path(ev["type"]),
                    "label": ev["type"],
                })

    rows = []
    for model in result_list:
        row = []
        for col in active_columns:
            key = col["key"]
            if key == "evidence":
                row.append({
                    "is_evidence": True,
                    "tiles": evidence_map.get(model.model_param_link_id, []),
                })
            elif key == "candidate_name":
                val = model.model_param_link.candidate_name
                row.append({"is_evidence": False, "value": val or "-"})
            elif key == "ned_name":
                val = model.model_param_link.ned_name
                row.append({"is_evidence": False, "value": val or "-"})
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


