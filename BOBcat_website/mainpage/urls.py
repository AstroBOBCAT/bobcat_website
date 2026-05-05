from django.urls import path

from . import views


urlpatterns = [
	path('', views.mainpage, name='main-page'),
	path('export/csv/', views.export_csv_view, name='export-csv'),
	path('export/json/', views.export_json_view, name='export-json'),
	path('code/', views.stub_code, name='code-page'),
	path('bobrefs/', views.stub_bobrefs, name='bobrefs-page'),
	path('classroom/', views.stub_classroom, name='classroom-page'),
]
