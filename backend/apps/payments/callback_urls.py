from django.urls import path

from . import callback_views

app_name = "payments_callback"

urlpatterns = [
    path("", callback_views.verify_callback, name="verify"),
]
