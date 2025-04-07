from typing import Any
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import DetailView
from django.views import View
from django.views.generic.edit import CreateView

from mainpage.models import source
# Create your views here.


def sourcepage(request, NED_name):
    source_search_result_data = source.objects.filter(NED_name = NED_name)
    return render(request, "sourcepage/sourcepage.html", {"source_data":source_search_result_data})
    
        

# class SourcepageView(TemplateView):
#     template_name = "sourcepage/sourcepage.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         loaded_source = self.object
#         request = self.request
#         NED_name = request.POST["NED_name"]
#         context["NED_name"] = NED_name
#         return context

  
