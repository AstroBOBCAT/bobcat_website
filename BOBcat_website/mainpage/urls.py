from django.urls import path

from . import views

#The binary-model-search is on the frontpage which is why its route is ''
urlpatterns = [
	path('', views.binary_model_search, name='binary-model-search'),
]
