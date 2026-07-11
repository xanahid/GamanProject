from datetime import datetime, timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.therapists.models import TherapistProfile
from .models import (
    Booking,
    NotifyRequest,
    RecurringBooking,
    SessionSlot,
    SLOT_STATUS_BOOKED,
    SLOT_STATUS_FREE,
    SLOT_STATUS_PENDING,
)
from .serializers import BookingCreateSerializer, BookingSerializer, NotifyRequestSerializer, SessionSlotSerializer


class MyBookingRouteView(APIView):
    """
    GET /api/v1/scheduling/my-route/

    Tells the client-side "book a session" button where to send the user:
    - First-time client (no completed intake session) -> Dr. Akbarzadeh's
      schedule, always, regardless of what they click.
    - Returning client with a recommended therapist -> that therapist's
      schedule directly.
    - Returning client with no recommendation yet (e.g. still mid-intake
      process) -> back to Dr. Akbarzadeh.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_client:
            raise PermissionDenied("فقط مراجعه‌کنندگان می‌توانند جلسه رزرو کنند.")

        profile = request.user.client_profile
        if not profile.has_completed_intake_session:
            head = TherapistProfile.objects.filter(is_head_of_institute=True, is_active=True).first()
            return Response({"therapist_id": head.id if head else None, "reason": "first_session"})

        if profile.recommended_therapist_id:
            return Response({"therapist_id": profile.recommended_therapist_id, "reason": "recommended"})

        head = TherapistProfile.objects.filter(is_head_of_institute=True, is_active=True).first()
        return Response({"therapist_id": head.id if head else None, "reason": "awaiting_recommendation"})


class TherapistDaySlotsView(APIView):
    """
    GET /api/v1/scheduling/therapists/<id>/day/?date=YYYY-MM-DD

    Returns one day's worth of 50-minute slots for the schedule grid widget.
    Patient names are only included when the requester IS that therapist.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, therapist_id):
        therapist = get_object_or_404(TherapistProfile, pk=therapist_id, is_active=True)
        date_str = request.query_params.get("date")
        if not date_str:
            raise ValidationError({"date": "این پارامتر الزامی است (YYYY-MM-DD)."})
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError({"date": "قالب تاریخ نامعتبر است."})

        viewer_is_therapist = (
            request.user.is_therapist and getattr(request.user, "therapist_profile", None) == therapist
        )

        slots = (
            SessionSlot.objects.filter(therapist=therapist, date=target_date)
            .select_related("booking__client")
            .order_by("start_time")
        )
        # Lazily release any holds that expired since the last sweep, so the
        # grid never shows a stale yellow to a viewer who refreshes.
        for slot in slots:
            if slot.is_hold_expired:
                slot.release_hold()

        data = SessionSlotSerializer(
            slots, many=True, context={"viewer_is_therapist": viewer_is_therapist}
        ).data
        return Response({
            "therapist_id": therapist.id,
            "date": date_str,
            "viewer_role": "therapist" if viewer_is_therapist else "client",
            "slots": data,
        })


class BookingCreateView(APIView):
    """
    POST /api/v1/scheduling/book/  {slot_id, make_weekly_recurring}

    Places a 15-minute payment hold (slot -> pending/yellow) and creates an
    AWAITING_PAYMENT Booking. Actual confirmation happens in the payments
    app once ZarinPal verifies the transaction. This view never marks a
    slot as paid/booked itself.
    """

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if not request.user.is_client:
            raise PermissionDenied("فقط مراجعه‌کنندگان می‌توانند جلسه رزرو کنند.")

        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot_id = serializer.validated_data["slot_id"]
        make_weekly = serializer.validated_data["make_weekly_recurring"]

        slot = get_object_or_404(SessionSlot.objects.select_for_update(), pk=slot_id)

        if slot.is_hold_expired:
            slot.release_hold()

        if slot.status == SLOT_STATUS_BOOKED:
            raise ValidationError("این زمان قبلاً رزرو و پرداخت شده است.")
        if slot.status == SLOT_STATUS_PENDING and slot.held_by_id and slot.held_by_id != request.user.id:
            raise ValidationError("این زمان در حال حاضر توسط فرد دیگری در حال رزرو است. لطفاً کمی صبر کنید.")

        profile = request.user.client_profile
        is_first_session = not profile.has_completed_intake_session

        slot.place_payment_hold(request.user)

        booking, _ = Booking.objects.update_or_create(
            slot=slot,
            defaults={
                "client": request.user,
                "therapist": slot.therapist,
                "status": Booking.Status.AWAITING_PAYMENT,
                "is_weekly_recurring": make_weekly,
                "is_first_session": is_first_session,
            },
        )

        if make_weekly:
            RecurringBooking.objects.get_or_create(
                client=request.user,
                therapist=slot.therapist,
                weekday=_python_weekday_to_choice(slot.date.weekday()),
                start_time=slot.start_time,
                defaults={"end_time": slot.end_time, "is_active": True},
            )

        return Response(
            {
                "booking": BookingSerializer(booking).data,
                "hold_expires_at": slot.hold_expires_at,
                "next_step": "proceed_to_payment",
            },
            status=status.HTTP_201_CREATED,
        )


def _python_weekday_to_choice(python_weekday):
    python_to_ours = {5: 0, 6: 1, 0: 2, 1: 3, 2: 4, 3: 5, 4: 6}
    return python_to_ours[python_weekday]


class BookingCancelView(APIView):
    """
    POST /api/v1/scheduling/bookings/<id>/cancel/

    Applies the spec's two cancellation policies depending on who's
    cancelling. The refund itself is handled by the payments app (this view
    just flags eligibility); salary impact is queued for Dr. Akbarzadeh's
    review in the payroll app when a therapist cancels late.
    """

    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, booking_id):
        booking = get_object_or_404(
            Booking.objects.select_related("slot", "therapist__user", "client"), pk=booking_id
        )
        user = request.user

        is_client_cancelling = user == booking.client
        is_therapist_cancelling = user.is_therapist and user.therapist_profile == booking.therapist

        if not (is_client_cancelling or is_therapist_cancelling):
            raise PermissionDenied("شما اجازه لغو این جلسه را ندارید.")

        if booking.status not in (Booking.Status.CONFIRMED, Booking.Status.AWAITING_PAYMENT):
            raise ValidationError("این جلسه قابل لغو نیست.")

        hours_left = booking.hours_until_session

        if is_client_cancelling:
            booking.status = Booking.Status.CANCELLED_BY_CLIENT
            refund_eligible = hours_left >= 24
            booking.cancelled_at = timezone.now()
            booking.cancelled_by = user
            booking.save(update_fields=["status", "cancelled_at", "cancelled_by", "updated_at"])
            booking.slot.status = SLOT_STATUS_FREE
            booking.slot.held_by = None
            booking.slot.save(update_fields=["status", "held_by", "updated_at"])

            if refund_eligible and booking.status == Booking.Status.CANCELLED_BY_CLIENT:
                from apps.payments.tasks import process_refund_for_booking
                process_refund_for_booking.delay(str(booking.id))

            return Response({
                "status": booking.status,
                "refund_eligible": refund_eligible,
                "message": (
                    "جلسه لغو شد و مبلغ به کارت شما بازگردانده می‌شود."
                    if refund_eligible else
                    "جلسه لغو شد. از آنجا که کمتر از ۲۴ ساعت به جلسه باقی مانده بود، مبلغ بازگردانده نمی‌شود."
                ),
            })

        # Therapist cancelling
        from apps.payroll.models import TherapistCancellation
        days_before = hours_left / 24
        TherapistCancellation.objects.create(
            booking=booking,
            therapist=booking.therapist,
            days_before_session=round(days_before, 2),
            salary_safe=days_before >= 4,
            # Final call always belongs to Dr. Akbarzadeh per spec, so this
            # starts as a pending review item even when >=4 days out.
            decided_by_head=False,
        )
        booking.status = Booking.Status.CANCELLED_BY_THERAPIST
        booking.cancelled_at = timezone.now()
        booking.cancelled_by = user
        booking.save(update_fields=["status", "cancelled_at", "cancelled_by", "updated_at"])
        booking.slot.status = SLOT_STATUS_FREE
        booking.slot.held_by = None
        booking.slot.save(update_fields=["status", "held_by", "updated_at"])

        from apps.payments.tasks import process_refund_for_booking
        process_refund_for_booking.delay(str(booking.id))

        return Response({
            "status": booking.status,
            "message": "جلسه توسط درمانگر لغو شد. تصمیم نهایی درباره اثر آن بر حقوق با دکتر اکبرزاده است.",
        })


class NotifyMeView(APIView):
    """
    POST /api/v1/scheduling/notify-me/  {therapist, weekday, start_time}
    DELETE same body — turns the "let me know if this opens up" alert on/off
    for a specific recurring weekday+time slot with a therapist.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = NotifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj, created = NotifyRequest.objects.update_or_create(
            client=request.user,
            therapist=serializer.validated_data["therapist"],
            weekday=serializer.validated_data["weekday"],
            start_time=serializer.validated_data["start_time"],
            defaults={"is_active": True},
        )
        return Response(NotifyRequestSerializer(obj).data, status=status.HTTP_201_CREATED if created else 200)

    def delete(self, request):
        NotifyRequest.objects.filter(
            client=request.user,
            therapist_id=request.data.get("therapist"),
            weekday=request.data.get("weekday"),
            start_time=request.data.get("start_time"),
        ).update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyBookingsView(APIView):
    """GET /api/v1/scheduling/my-bookings/ — client's own bookings, used by profile page."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bookings = (
            Booking.objects.filter(client=request.user)
            .select_related("slot", "therapist__user")
            .order_by("-slot__date", "-slot__start_time")
        )
        return Response(BookingSerializer(bookings, many=True).data)
