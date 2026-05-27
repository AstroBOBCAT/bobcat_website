from django.http import JsonResponse
from django.shortcuts import render
from .models import BinaryModel, Papers

#A simple prototype for the frontend. Don't worry about this structure its not representative of the final product.
#Also if you want to replace this entire thing thats fine.

ALL_COLUMNS = [
    {"key": "candidate_name", "label": "Candidate",          "default": True},
    {"key": "ned_name",       "label": "NED Name",           "default": True},
    {"key": "paper",          "label": "Paper",              "default": True},
    {"key": "sheet_id",       "label": "Sheet ID",           "default": False},
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

TEXT_FIELDS = [
    "sheet_id",
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

#The primary method that returns the information in the mainpage.
def binary_model_search(request):
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

    rows = []
    for model in results:
        row = []
        for col in active_columns:
            key = col["key"]
            if key == "candidate_name":
                val = model.model_param_link.candidate_name
            elif key == "ned_name":
                val = model.model_param_link.ned_name
            else:
                val = getattr(model, key, None)
            row.append(val if val is not None and val != "" else "-")
        rows.append(row)

    context = {
        "rows": rows,
        "result_count": len(rows),
        "has_query": has_query,
        "active_columns": active_columns,
        "all_columns": [
            {**col, "checked": col["key"] in active_key_set}
            for col in ALL_COLUMNS
        ],
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
    }
    return render(request, "mainpage/binary_model_search.html", context)


