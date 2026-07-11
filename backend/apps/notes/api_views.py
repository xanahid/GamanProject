from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import SessionNote
from .serializers import SessionNoteSerializer


class IsTherapistUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_therapist)


class ClientNotesListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/notes/clients/<client_id>/?therapist=<id>
    POST /api/v1/notes/clients/<client_id>/

    A therapist only ever sees/creates notes for clients they themselves
    treat — scoping is enforced here, not trusted from the client. Dr.
    Akbarzadeh (is_head_of_institute) can view (read-only via this
    endpoint) any client's notes across therapists, matching the spec's
    "she can review the notes... of each therapist."
    """

    serializer_class = SessionNoteSerializer
    permission_classes = [IsTherapistUser]

    def get_queryset(self):
        client_id = self.kwargs["client_id"]
        therapist_profile = self.request.user.therapist_profile
        qs = SessionNote.objects.filter(client_id=client_id).select_related("therapist__user")
        if not therapist_profile.is_head_of_institute:
            qs = qs.filter(therapist=therapist_profile)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        from apps.scheduling.models import Booking
        therapist_profile = self.request.user.therapist_profile
        client_id = self.kwargs["client_id"]

        # A therapist may only write a note for a client they have an
        # actual (current or past) booking relationship with.
        has_relationship = Booking.objects.filter(
            therapist=therapist_profile, client_id=client_id
        ).exists()
        if not has_relationship and not therapist_profile.is_head_of_institute:
            raise PermissionDenied("شما با این مراجع جلسه‌ای نداشته‌اید.")

        serializer.save(therapist=therapist_profile, client_id=client_id)


class SessionNoteDetailView(generics.RetrieveUpdateAPIView):
    """Edit a single note — only the authoring therapist or the head of institute."""

    serializer_class = SessionNoteSerializer
    permission_classes = [IsTherapistUser]

    def get_queryset(self):
        therapist_profile = self.request.user.therapist_profile
        qs = SessionNote.objects.all()
        if not therapist_profile.is_head_of_institute:
            qs = qs.filter(therapist=therapist_profile)
        return qs
