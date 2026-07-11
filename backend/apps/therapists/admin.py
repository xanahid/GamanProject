from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.utils import timezone

from .models import Department, Specialty, TherapistProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "order")
    list_filter = ("department",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    """
    This is the surface Dr. Akbarzadeh uses (per the spec) to review every
    therapist's profile and see hours worked in the last 6 months — the
    `sessions_last_6_months` column below is computed live from booked
    sessions, not stored, so it's always accurate.
    """

    list_display = (
        "user", "is_head_of_institute", "years_active", "active_client_count",
        "sessions_last_6_months", "is_active",
    )
    list_filter = ("is_active", "is_head_of_institute", "departments", "specialties")
    search_fields = ("user__first_name", "user__last_name", "user__email")
    autocomplete_fields = ("user",)
    filter_horizontal = ("specialties", "departments")

    def get_queryset(self, request):
        six_months_ago = timezone.now().date() - timedelta(days=182)
        qs = super().get_queryset(request)
        return qs.annotate(
            _sessions_6mo=Count(
                "bookings",
                filter=models_q_booked_since(six_months_ago),
            )
        )

    @admin.display(description="جلسات ۶ ماه اخیر")
    def sessions_last_6_months(self, obj):
        return getattr(obj, "_sessions_6mo", 0)


def models_q_booked_since(since_date):
    from django.db.models import Q

    from apps.scheduling.models import SLOT_STATUS_BOOKED

    return Q(bookings__slot__status=SLOT_STATUS_BOOKED, bookings__slot__date__gte=since_date)
