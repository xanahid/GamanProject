from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.therapists.models import TherapistProfile
from apps.scheduling.models import Booking, SLOT_STATUS_BOOKED
from apps.notes.models import SessionNote
from apps.content.models import Article


@login_required
def head_dashboard(request):
    """
    Dr. Akbarzadeh's front-end panel — only accessible to therapists
    with is_head_of_institute=True. Shows all therapists, their sessions,
    notes browser, and content management shortcuts.
    """
    if not request.user.is_authenticated:
        return redirect("accounts:login")

    # Only head of institute can access this
    profile = getattr(request.user, "therapist_profile", None)
    if not profile or not profile.is_head_of_institute:
        return redirect("core:home")

    therapists = (
        TherapistProfile.objects.filter(is_active=True)
        .select_related("user")
        .prefetch_related("specialties")
        .order_by("-is_head_of_institute", "user__first_name")
    )

    recent_bookings = (
        Booking.objects.filter(status=Booking.Status.CONFIRMED)
        .select_related("client", "therapist__user", "slot")
        .order_by("-slot__date", "-slot__start_time")[:20]
    )

    recent_notes = (
        SessionNote.objects.all()
        .select_related("therapist__user", "client")
        .order_by("-created_at")[:10]
    )

    articles = Article.objects.all().order_by("-published_at")[:5]

    return render(request, "home/head_dashboard.html", {
        "therapists": therapists,
        "recent_bookings": recent_bookings,
        "recent_notes": recent_notes,
        "articles": articles,
    })
