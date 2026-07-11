from django.contrib import admin

from .models import Booking, NotifyRequest, PushSubscription, RecurringBooking, SessionSlot, WeeklyAvailability


@admin.register(WeeklyAvailability)
class WeeklyAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("therapist", "get_weekday_display", "start_time", "end_time", "is_active")
    list_filter = ("weekday", "is_active", "therapist")
    autocomplete_fields = ("therapist",)

    @admin.display(description="روز هفته")
    def get_weekday_display(self, obj):
        return obj.get_weekday_display()


@admin.register(SessionSlot)
class SessionSlotAdmin(admin.ModelAdmin):
    list_display = ("therapist", "date", "start_time", "status", "is_recurring_hold", "held_by")
    list_filter = ("status", "is_recurring_hold", "date", "therapist")
    date_hierarchy = "date"
    autocomplete_fields = ("therapist", "held_by")
    search_fields = ["client__first_name", "client__last_name"]


@admin.register(RecurringBooking)
class RecurringBookingAdmin(admin.ModelAdmin):
    list_display = ("client", "therapist", "weekday", "start_time", "is_active")
    list_filter = ("weekday", "is_active")
    autocomplete_fields = ("client", "therapist")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Dr. Akbarzadeh's window into every booking: status, schedule, who
    cancelled and when (feeds the payroll deduction decision).
    """

    list_display = ("client", "therapist", "slot", "status", "is_weekly_recurring", "is_first_session")
    list_filter = ("status", "is_weekly_recurring", "is_first_session", "therapist")
    search_fields = ("client__first_name", "client__last_name", "therapist__user__first_name")
    autocomplete_fields = ("client", "therapist", "slot", "cancelled_by")
    readonly_fields = ("cancelled_at",)


@admin.register(NotifyRequest)
class NotifyRequestAdmin(admin.ModelAdmin):
    list_display = ("client", "therapist", "weekday", "start_time", "is_active", "notified_at")
    list_filter = ("weekday", "is_active")


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "endpoint", "created_at")
