from django.shortcuts import get_object_or_404, render

from .models import Department, Specialty, TherapistProfile


def directory(request):
    """درمانگران گمان — list of blocks with picture + bio, click -> profile."""
    therapists = (
        TherapistProfile.objects.filter(is_active=True)
        .select_related("user")
        .prefetch_related("specialties")
        .order_by("-is_head_of_institute", "-years_active")
    )
    departments = Department.objects.all()
    specialties = Specialty.objects.all()
    return render(
        request,
        "therapists/directory.html",
        {"therapists": therapists, "departments": departments, "specialties": specialties},
    )


def detail(request, pk):
    therapist = get_object_or_404(
        TherapistProfile.objects.select_related("user").prefetch_related("specialties", "departments"),
        pk=pk, is_active=True,
    )
    return render(request, "therapists/detail.html", {"therapist": therapist})
