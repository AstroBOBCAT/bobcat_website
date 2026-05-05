from django.urls import path

from . import views


# urlpatterns = [
#     path("", views.MainpageView.as_view(), name = "main-page")
# ]

urlpatterns = [
    path("", views.mainpage, name = "main-page")
]