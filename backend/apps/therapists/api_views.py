from rest_framework import generics, permissions

from .models import TherapistProfile
from .serializers import TherapistDetailSerializer, TherapistListSerializer


class TherapistListAPIView(generics.ListAPIView):
    """GET /api/v1/therapists/ — full directory, used by the 'درمانگران گمان' page."""

    serializer_class = TherapistListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = TherapistProfile.objects.filter(is_active=True).select_related("user").prefetch_related("specialties")


class TherapistDetailAPIView(generics.RetrieveAPIView):
    serializer_class = TherapistDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = TherapistProfile.objects.filter(is_active=True).select_related("user").prefetch_related(
        "specialties", "departments"
    )
