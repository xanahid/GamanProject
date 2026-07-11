from django.urls import path

from apps.realtime import api_views as realtime_api_views

from . import api_views

app_name = "scheduling_api"

urlpatterns = [
    path("my-route/", api_views.MyBookingRouteView.as_view(), name="my_route"),
    path("therapists/<int:therapist_id>/day/", api_views.TherapistDaySlotsView.as_view(), name="therapist_day"),
    path("book/", api_views.BookingCreateView.as_view(), name="book"),
    path("bookings/<uuid:booking_id>/cancel/", api_views.BookingCancelView.as_view(), name="cancel"),
    path("notify-me/", api_views.NotifyMeView.as_view(), name="notify_me"),
    path("my-bookings/", api_views.MyBookingsView.as_view(), name="my_bookings"),
    path("push/subscribe/", realtime_api_views.PushSubscribeView.as_view(), name="push_subscribe"),
    path("push/unsubscribe/", realtime_api_views.PushUnsubscribeView.as_view(), name="push_unsubscribe"),
]
