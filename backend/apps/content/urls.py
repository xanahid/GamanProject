from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("<slug:slug>/", views.article_detail, name="article_detail"),
]
