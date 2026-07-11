from rest_framework import serializers

from .models import Booking, NotifyRequest, RecurringBooking, SessionSlot


class SessionSlotSerializer(serializers.ModelSerializer):
    """
    Same underlying status, audience-specific color is computed client-side
    (React just maps status -> {client: white|yellow|red, therapist:
    white|yellow|green}) so we don't need two serializers for one slot.
    """

    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = SessionSlot
        fields = [
            "id", "date", "start_time", "end_time", "status",
            "is_recurring_hold", "patient_name",
        ]

    def get_patient_name(self, obj):
        # Only exposed when the requesting user IS the therapist of this
        # slot — enforced in the view's queryset/context, not here, but we
        # double-check via context flag for defense in depth.
        if self.context.get("viewer_is_therapist") and hasattr(obj, "booking"):
            return obj.booking.client.get_full_name()
        return None


class BookingCreateSerializer(serializers.Serializer):
    slot_id = serializers.UUIDField()
    make_weekly_recurring = serializers.BooleanField(default=False)


class BookingSerializer(serializers.ModelSerializer):
    therapist_name = serializers.CharField(source="therapist.user.get_full_name", read_only=True)
    client_name = serializers.CharField(source="client.get_full_name", read_only=True)
    date = serializers.DateField(source="slot.date", read_only=True)
    start_time = serializers.TimeField(source="slot.start_time", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "therapist", "therapist_name", "client_name", "date",
            "start_time", "status", "is_weekly_recurring", "is_first_session",
            "created_at",
        ]


class NotifyRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotifyRequest
        fields = ["id", "therapist", "weekday", "start_time", "is_active"]
        read_only_fields = ["id"]
