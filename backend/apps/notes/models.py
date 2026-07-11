from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class SessionNote(TimeStampedModel):
    """
    Private clinical note a therapist writes after/during a session with a
    client. Per spec: clicking a patient's name on the therapist's own
    schedule opens this. Dr. Akbarzadeh (head of institute) can review
    notes across all therapists; any other therapist can only see notes
    they personally authored.
    """

    booking = models.OneToOneField(
        "scheduling.Booking", on_delete=models.CASCADE, related_name="note", null=True, blank=True,
        help_text="یادداشت مرتبط با یک جلسه مشخص",
    )
    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="session_notes"
    )
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_notes")
    content = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"یادداشت {self.therapist} درباره {self.client} — {self.created_at:%Y-%m-%d}"
