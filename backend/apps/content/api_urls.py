from django.urls import path

from . import api_views

app_name = "content_api"

urlpatterns = [
    path("articles/", api_views.ArticleListAPIView.as_view(), name="articles"),
    path("methods/", api_views.TherapyMethodListAPIView.as_view(), name="methods"),
    path("sections/", api_views.HomepageSectionListAPIView.as_view(), name="sections"),
]
