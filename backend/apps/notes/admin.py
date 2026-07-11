from django.contrib import admin

from .models import SessionNote


@admin.register(SessionNote)
class SessionNoteAdmin(admin.ModelAdmin):
    """
    Per spec, Dr. Akbarzadeh "can review the notes... of each therapist."
    Regular therapists should only manage their own notes via the
    front-end note-taking panel (React widget, not this admin); this
    admin view is restricted to staff (Dr. Akbarzadeh has is_staff=True).
    """

    list_display = ("client", "therapist", "created_at")
    list_filter = ("therapist",)
    search_fields = ("client__first_name", "client__last_name", "content")
    autocomplete_fields = ("client", "therapist", "booking")

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff
