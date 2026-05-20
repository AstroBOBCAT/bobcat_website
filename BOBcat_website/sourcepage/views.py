from typing import Any
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.views import View
from django.views.generic.edit import CreateView

from sourcepage.models import BinaryModel, Papers
# Create your views here.


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
    source_search_result_data = Papers.objects.filter(candidate_name = name)
    return render(request, "sourcepage/sourcepage.html", {"source_data":source_search_result_data})


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

    has_query = any(value for value in request.GET.values())

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

    context = {
        "results": results,
        "has_query": has_query,
        "float_fields": [
            {"name": field, "label": FLOAT_FIELD_LABELS[field]}
            for field in FLOAT_FIELDS
        ],
        "text_fields": [
            {"name": field, "label": TEXT_FIELD_LABELS[field]}
            for field in TEXT_FIELDS
        ],
    }
    return render(request, "sourcepage/binary_model_search.html", context)
    
        

# class SourcepageView(TemplateView):
#     template_name = "sourcepage/sourcepage.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         loaded_source = self.object
#         request = self.request
#         NED_name = request.POST["NED_name"]
#         context["NED_name"] = NED_name
#         return context

  
