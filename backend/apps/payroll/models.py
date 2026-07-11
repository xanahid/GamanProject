from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class TherapistCancellation(TimeStampedModel):
    """
    Logged automatically whenever a therapist cancels a booked session
    (see scheduling.api_views.BookingCancelView). `salary_safe` is the
    *computed* default per the spec's 4-day rule, but the actual financial
    outcome always waits on `decided_by_head` — Dr. Akbarzadeh has the
    final say per spec, even when the computed rule would protect the
    therapist's pay.
    """

    booking = models.OneToOneField(
        "scheduling.Booking", on_delete=models.CASCADE, related_name="cancellation_record"
    )
    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="cancellations"
    )
    days_before_session = models.DecimalField(max_digits=6, decimal_places=2)
    salary_safe = models.BooleanField(
        default=True, help_text="محاسبه‌شده بر اساس قانون ۴ روز — تصمیم نهایی نیست"
    )

    decided_by_head = models.BooleanField(default=False, help_text="آیا دکتر اکبرزاده تصمیم نهایی را ثبت کرده؟")
    final_salary_deduction_applied = models.BooleanField(default=False)
    deduction_amount_rials = models.PositiveBigIntegerField(default=0)
    head_notes = models.TextField(blank=True, help_text="یادداشت دکتر اکبرزاده درباره این تصمیم")
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"لغو توسط {self.therapist} — {self.days_before_session} روز قبل"


class MonthlyPayrollSummary(TimeStampedModel):
    """
    Optional rollup used by Dr. Akbarzadeh's dashboard to see a therapist's
    total session hours and any deductions for a given month at a glance.
    Generated/refreshed by a Celery task rather than computed on every page
    load.
    """

    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="payroll_summaries"
    )
    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    completed_sessions = models.PositiveIntegerField(default=0)
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    base_salary_rials = models.PositiveBigIntegerField(default=0)
    total_deductions_rials = models.PositiveBigIntegerField(default=0)

    class Meta:
        unique_together = ("therapist", "year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.therapist} — {self.year}/{self.month}"

    @property
    def final_payout_rials(self):
        return max(self.base_salary_rials - self.total_deductions_rials, 0)
