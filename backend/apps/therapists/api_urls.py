from django.urls import path

from . import api_views

app_name = "therapists_api"

urlpatterns = [
    path("", api_views.TherapistListAPIView.as_view(), name="list"),
    path("<int:pk>/", api_views.TherapistDetailAPIView.as_view(), name="detail"),
]
