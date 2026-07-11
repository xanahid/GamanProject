from django.urls import path

from . import api_views

app_name = "notes_api"

urlpatterns = [
    path("clients/<int:client_id>/", api_views.ClientNotesListCreateView.as_view(), name="client_notes"),
    path("<int:pk>/", api_views.SessionNoteDetailView.as_view(), name="note_detail"),
]
