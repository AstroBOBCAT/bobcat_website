from django.shortcuts import render

# Create your views here.


def aboutpage(request):
    return render(request, "aboutpage/about.html")