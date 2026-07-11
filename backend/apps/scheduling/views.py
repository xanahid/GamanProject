from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.therapists.models import TherapistProfile


@login_required
def book_session_entry(request):
    """
    /accounts is where login lives, but the *booking* entry point is what
    the spec calls "if its the users first time trying to book a session" —
    this view doesn't render the grid itself, it just resolves which
    therapist's schedule to show (head of institute vs recommended
    therapist) and redirects into therapist_schedule_client below. The
    React widget also calls /api/v1/scheduling/my-route/ directly for
    in-page navigation without a full reload; this view exists for the
    bookmarkable/direct-link case.
    """
    if not request.user.is_client:
        return redirect("core:home")

    profile = request.user.client_profile
    if profile.has_completed_intake_session and profile.recommended_therapist_id:
        return redirect("scheduling:client_schedule", therapist_id=profile.recommended_therapist_id)

    head = TherapistProfile.objects.filter(is_head_of_institute=True, is_active=True).first()
    if head is None:
        return redirect("core:home")
    return redirect("scheduling:client_schedule", therapist_id=head.id)


@login_required
def client_schedule_view(request, therapist_id):
    """Renders the page shell + mounts <ScheduleWidget mode='client'> for this therapist."""
    therapist = get_object_or_404(TherapistProfile, pk=therapist_id, is_active=True)
    return render(request, "home/schedule_page.html", {
        "therapist": therapist,
        "widget_mode": "client",
        "session_price": settings.SESSION_PRICE_RIALS,
    })


@login_required
def therapist_schedule_view(request):
    """Renders the page shell + mounts <ScheduleWidget mode='therapist'> for the logged-in therapist."""
    if not request.user.is_therapist:
        return redirect("core:home")
    therapist = request.user.therapist_profile
    return render(request, "home/schedule_page.html", {
        "therapist": therapist,
        "widget_mode": "therapist",
        "session_price": settings.SESSION_PRICE_RIALS,
    })
