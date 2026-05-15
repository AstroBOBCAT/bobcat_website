from django.urls import path

from . import views


urlpatterns = [
	path('', views.binary_model_list, name='main-page')
]
