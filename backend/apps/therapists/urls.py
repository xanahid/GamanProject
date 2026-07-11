from django.urls import path

from . import views

app_name = "therapists"

urlpatterns = [
    path("", views.directory, name="directory"),
    path("<int:pk>/", views.detail, name="detail"),
]
