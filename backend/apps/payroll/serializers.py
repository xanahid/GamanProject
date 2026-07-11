from rest_framework import serializers

from .models import MonthlyPayrollSummary, TherapistCancellation


class TherapistCancellationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TherapistCancellation
        fields = [
            "id", "booking", "days_before_session", "salary_safe",
            "decided_by_head", "final_salary_deduction_applied",
            "deduction_amount_rials", "head_notes", "decided_at",
        ]
        read_only_fields = fields


class MonthlyPayrollSummarySerializer(serializers.ModelSerializer):
    final_payout_rials = serializers.IntegerField(read_only=True)

    class Meta:
        model = MonthlyPayrollSummary
        fields = [
            "year", "month", "completed_sessions", "total_hours",
            "base_salary_rials", "total_deductions_rials", "final_payout_rials",
        ]
