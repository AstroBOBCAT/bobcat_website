from django.urls import path

from . import views


urlpatterns = [
	path('', views.binary_model_search, name='main-page'),
]
