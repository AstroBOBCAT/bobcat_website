from django.urls import path

from . import views

app_name = 'show_models'

urlpatterns = [
    path("", views.modelshow, name = "modelshow")

]