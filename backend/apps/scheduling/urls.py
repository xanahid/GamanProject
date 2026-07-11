from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    path("book/", views.book_session_entry, name="book_entry"),
    path("book/<int:therapist_id>/", views.client_schedule_view, name="client_schedule"),
    path("my-schedule/", views.therapist_schedule_view, name="therapist_schedule"),
]
