from django.urls import path

from . import views


urlpatterns = [
	path('search/', views.binary_model_search, name='binary-model-search'),
	path('<str:name>/', views.sourcepage, name='source-page'),
]

# urlpatterns = [
#     path("<NED_name", views.SourcepageView.as_view(), name = "source-page")
# ]
