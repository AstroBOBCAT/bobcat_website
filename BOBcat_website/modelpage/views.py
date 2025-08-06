from django.shortcuts import render
from django.http import HttpResponse
from . models import model
 
# Create your views here.

def modelshow(request): #, query_id):
    query_name = request.GET.get("query_name")
    results_mod = model.objects.filter(source_name=query_name)
    #return HttpResponse(query_id)
    return render(request, "show_models/model_display.html", {"data_mod":results_mod})
