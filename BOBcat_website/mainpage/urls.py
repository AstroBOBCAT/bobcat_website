from django.urls import path

from . import views


urlpatterns = [
	path('', views.papers_list, name='main-page')
]
