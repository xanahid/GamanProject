from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/schedule/(?P<therapist_id>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$",
        consumers.ScheduleConsumer.as_asgi(),
    ),
    re_path(r"^ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
]
