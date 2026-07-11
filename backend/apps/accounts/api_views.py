from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import ClientProfile, SavedCard
from .serializers import ClientProfileSerializer, ClientSignupSerializer, SavedCardSerializer

User = get_user_model()


class SignupView(generics.CreateAPIView):
    """POST /api/v1/accounts/signup/ — public, creates a client account."""

    serializer_class = ClientSignupSerializer
    permission_classes = [permissions.AllowAny]


class FlexibleTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Lets a user log in with either their email or their phone number in the
    same "identifier" field, since the spec asks for a "pretty standard"
    login — most Iranian users expect phone-number login to just work.
    """

    username_field = "identifier"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["identifier"] = self.fields.pop(User.USERNAME_FIELD)

    def validate(self, attrs):
        identifier = attrs.get("identifier")
        user = (
            User.objects.filter(email__iexact=identifier).first()
            or User.objects.filter(phone_number=identifier).first()
        )
        if user is None:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed("کاربری با این مشخصات یافت نشد.")
        attrs[User.USERNAME_FIELD] = user.get_username()
        return super().validate(attrs)


class LoginView(TokenObtainPairView):
    serializer_class = FlexibleTokenObtainSerializer
    permission_classes = [permissions.AllowAny]


class MyProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/accounts/me/ — the logged-in client's own profile."""

    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.client_profile


class MyDashboardSummaryView(APIView):
    """
    Small aggregate used by the client's profile page: upcoming session,
    recommended therapist (if assigned), saved card count.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.scheduling.models import SLOT_STATUS_BOOKED, Booking
        import datetime

        user = request.user
        if not user.is_client:
            return Response({"detail": "فقط برای مراجعه‌کنندگان."}, status=status.HTTP_403_FORBIDDEN)

        profile = ClientProfile.objects.select_related("recommended_therapist__user").get(user=user)
        upcoming = (
            Booking.objects.filter(
                client=user, slot__status=SLOT_STATUS_BOOKED, slot__date__gte=datetime.date.today()
            )
            .select_related("slot", "therapist__user")
            .order_by("slot__date", "slot__start_time")
            .first()
        )

        return Response({
            "has_completed_intake_session": profile.has_completed_intake_session,
            "recommended_therapist": (
                {
                    "id": profile.recommended_therapist_id,
                    "name": profile.recommended_therapist.user.get_full_name(),
                }
                if profile.recommended_therapist_id else None
            ),
            "upcoming_session": (
                {
                    "date": upcoming.slot.date,
                    "start_time": upcoming.slot.start_time,
                    "therapist_name": upcoming.therapist.user.get_full_name(),
                    "is_weekly_recurring": upcoming.is_weekly_recurring,
                }
                if upcoming else None
            ),
            "saved_card_count": SavedCard.objects.filter(client=user).count(),
        })


class SavedCardListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedCard.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        if SavedCard.objects.filter(client=self.request.user).count() >= 5:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("حداکثر ۵ کارت قابل ذخیره است.")
        serializer.save(client=self.request.user)


class SavedCardDeleteView(generics.DestroyAPIView):
    serializer_class = SavedCardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedCard.objects.filter(client=self.request.user)
