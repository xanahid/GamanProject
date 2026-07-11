from django.urls import path

from . import views
from . import head_views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("methods/<slug:slug>/", views.therapy_method_detail, name="method_detail"),
    path("head/", head_views.head_dashboard, name="head_dashboard"),
]
