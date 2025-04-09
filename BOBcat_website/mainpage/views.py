from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic import ListView

from .models import Candidate, BinaryModel
from .forms import SearchForm

# Create your views here.



# class MainpageView(ListView):
#     template_name = "mainpage/main.html"
#     model = source
#     context_object_name = "sources"

# def mainpage(request):
#     return render(request, "mainpage/main.html")

def mainpage(request):
    form = SearchForm()
    sources_all = Candidate.objects.all()
    binary_models_all = BinaryModel.objects.all()
    if request.method=='POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            #now in the object cd, you have the form as a dictionary.
            a = cd.get('name')

    return render(request, "mainpage/main.html", {'form': form, 'sources' : sources_all, "binary_models" : binary_models_all})