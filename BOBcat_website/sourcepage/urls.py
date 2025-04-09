from django.urls import path

from . import views


urlpatterns = [
    path("<name>", views.sourcepage, name = "source-page")
]

# urlpatterns = [
#     path("<NED_name", views.SourcepageView.as_view(), name = "source-page")
# ]