from django.contrib import admin
from django.utils import timezone

from .models import MonthlyPayrollSummary, TherapistCancellation


@admin.register(TherapistCancellation)
class TherapistCancellationAdmin(admin.ModelAdmin):
    """
    This is where Dr. Akbarzadeh exercises the "final decision... in the
    hands of dr sarah akbarzadeh" rule from the spec: she reviews each
    therapist cancellation and explicitly decides the salary outcome,
    rather than the 4-day rule applying automatically and silently.
    """

    list_display = (
        "therapist", "booking", "days_before_session", "salary_safe",
        "decided_by_head", "final_salary_deduction_applied", "deduction_amount_rials",
    )
    list_filter = ("salary_safe", "decided_by_head", "final_salary_deduction_applied", "therapist")
    autocomplete_fields = ("booking", "therapist", "decided_by")
    readonly_fields = ("days_before_session", "salary_safe", "created_at")
    actions = ["approve_no_deduction", "apply_full_deduction"]

    @admin.action(description="تأیید: بدون کسر از حقوق")
    def approve_no_deduction(self, request, queryset):
        queryset.update(
            decided_by_head=True, final_salary_deduction_applied=False,
            deduction_amount_rials=0, decided_at=timezone.now(), decided_by=request.user,
        )

    @admin.action(description="اعمال کسر کامل از حقوق آن جلسه")
    def apply_full_deduction(self, request, queryset):
        for record in queryset:
            session_rate = record.therapist.monthly_base_salary // 30 if record.therapist.monthly_base_salary else 0
            record.decided_by_head = True
            record.final_salary_deduction_applied = True
            record.deduction_amount_rials = session_rate
            record.decided_at = timezone.now()
            record.decided_by = request.user
            record.save()


@admin.register(MonthlyPayrollSummary)
class MonthlyPayrollSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "therapist", "year", "month", "completed_sessions", "total_hours",
        "base_salary_rials", "total_deductions_rials", "final_payout_rials",
    )
    list_filter = ("year", "month", "therapist")
