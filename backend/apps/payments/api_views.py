from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import SavedCard
from apps.scheduling.models import Booking, SLOT_STATUS_PENDING
from .gateways.zarinpal import ZarinPalError, request_payment
from .models import Payment
from .serializers import PaymentInitiateSerializer, PaymentSerializer


class PaymentInitiateView(APIView):
    """
    POST /api/v1/payments/initiate/  {booking_id, saved_card_id?}

    Creates a Payment(pending) row and asks ZarinPal for a transaction
    `authority`, returning the URL the client's browser should navigate to
    (ZarinPal's own hosted, PCI-compliant payment page). We never see card
    digits ourselves. Throttled hard (see settings.REST_FRAMEWORK) since
    this is the single most sensitive endpoint in the app.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "payment_initiate"

    @transaction.atomic
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_object_or_404(
            Booking.objects.select_related("slot", "client", "therapist__user"),
            pk=serializer.validated_data["booking_id"],
        )
        if booking.client_id != request.user.id:
            raise PermissionDenied("این جلسه متعلق به شما نیست.")
        if booking.status != Booking.Status.AWAITING_PAYMENT:
            raise ValidationError("این جلسه در وضعیت قابل پرداخت نیست.")
        if booking.slot.status != SLOT_STATUS_PENDING:
            raise ValidationError("نگه‌داری زمان این جلسه منقضی شده است. لطفاً دوباره انتخاب کنید.")

        saved_card = None
        saved_card_id = serializer.validated_data.get("saved_card_id")
        if saved_card_id:
            saved_card = get_object_or_404(SavedCard, pk=saved_card_id, client=request.user)

        amount = settings.SESSION_PRICE_RIALS

        payment = Payment.objects.create(
            booking=booking,
            client=request.user,
            amount_rials=amount,
            status=Payment.Status.PENDING,
            saved_card_used=saved_card,
        )

        callback_url = request.build_absolute_uri(reverse("payments_callback:verify"))
        try:
            result = request_payment(
                amount_rials=amount,
                description=f"جلسه درمانی گمان — {booking.therapist.user.get_full_name()}",
                callback_url=f"{callback_url}?payment_id={payment.id}",
                mobile=str(request.user.phone_number or ""),
                email=request.user.email,
            )
        except ZarinPalError as exc:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = str(exc)
            payment.save(update_fields=["status", "failure_reason", "updated_at"])
            raise ValidationError(f"اتصال به درگاه پرداخت ناموفق بود: {exc}")

        payment.authority = result["authority"]
        payment.save(update_fields=["authority", "updated_at"])

        return Response(
            {"payment": PaymentSerializer(payment).data, "redirect_url": result["redirect_url"]},
            status=status.HTTP_201_CREATED,
        )


class MyCardsForCheckoutView(APIView):
    """GET /api/v1/payments/checkout-cards/ — saved cards shown at the 'choose a card' step."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.accounts.serializers import SavedCardSerializer
        cards = SavedCard.objects.filter(client=request.user)
        return Response(SavedCardSerializer(cards, many=True).data)
