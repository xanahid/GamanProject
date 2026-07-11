from rest_framework import generics, permissions

from .models import MonthlyPayrollSummary, TherapistCancellation
from .serializers import MonthlyPayrollSummarySerializer, TherapistCancellationSerializer


class MyPayrollSummaryView(generics.ListAPIView):
    """GET /api/v1/payroll/my-summaries/ — therapist's own monthly payout history."""

    serializer_class = MonthlyPayrollSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MonthlyPayrollSummary.objects.filter(therapist=self.request.user.therapist_profile)


class MyCancellationsView(generics.ListAPIView):
    """GET /api/v1/payroll/my-cancellations/ — therapist's own cancellation/deduction history."""

    serializer_class = TherapistCancellationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TherapistCancellation.objects.filter(therapist=self.request.user.therapist_profile)
