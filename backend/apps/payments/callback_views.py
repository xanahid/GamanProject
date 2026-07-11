from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from apps.scheduling.models import Booking, SLOT_STATUS_BOOKED
from .gateways.zarinpal import ZarinPalError, verify_payment
from .models import Payment


@require_GET
@csrf_exempt
def verify_callback(request):
    """
    GET /payments/verify/?Authority=...&Status=OK&payment_id=...

    This is the ONLY place a slot ever transitions to booked/paid. We:
      1. Look up the Payment row by the id we embedded in callback_url.
      2. Check ZarinPal's `Status` query param — if it's not OK, the user
         cancelled or the bank declined; mark failed, release the slot
         hold, bounce back to the booking page with an error.
      3. If Status=OK, call ZarinPal's verify.json endpoint SERVER-TO-SERVER
         (never trust the redirect alone — that query string is
         client-controlled and could be forged) with the exact amount we
         charged. Only on a verified 100/101 response do we mark the
         booking confirmed and the slot booked.
      4. Everything happens inside one DB transaction with a row lock on
         the slot, so two browser tabs can't both win the same slot.
    """
    payment_id = request.GET.get("payment_id")
    authority = request.GET.get("Authority", "")
    gateway_status = request.GET.get("Status", "")

    payment = get_object_or_404(Payment.objects.select_related("booking__slot", "booking__client"), pk=payment_id)

    # Idempotency: if this payment was already verified (user refreshed the
    # callback page, or ZarinPal retried the redirect), don't double-charge
    # logic — just show the existing result.
    if payment.status == Payment.Status.SUCCESS:
        return render(request, "content/payment_result.html", {"success": True, "booking": payment.booking})

    if gateway_status != "OK" or payment.authority != authority:
        payment.status = Payment.Status.FAILED
        payment.failure_reason = "کاربر پرداخت را لغو کرد یا تراکنش توسط بانک رد شد."
        payment.save(update_fields=["status", "failure_reason", "updated_at"])
        _release_slot_hold(payment.booking)
        return render(request, "content/payment_result.html", {"success": False, "booking": payment.booking})

    try:
        with transaction.atomic():
            slot = type(payment.booking.slot).objects.select_for_update().get(pk=payment.booking.slot_id)

            result = verify_payment(amount_rials=payment.amount_rials, authority=authority)

            payment.status = Payment.Status.SUCCESS
            payment.ref_id = result["ref_id"]
            payment.card_pan_masked = result["card_pan"]
            payment.paid_at = __import__("django.utils.timezone", fromlist=["timezone"]).now()
            payment.save(update_fields=["status", "ref_id", "card_pan_masked", "paid_at", "updated_at"])

            slot.mark_booked(payment.booking.client)

            booking = payment.booking
            booking.status = Booking.Status.CONFIRMED
            booking.save(update_fields=["status", "updated_at"])

            if booking.is_first_session:
                profile = booking.client.client_profile
                profile.has_completed_intake_session = True
                profile.save(update_fields=["has_completed_intake_session", "updated_at"])

    except ZarinPalError as exc:
        payment.status = Payment.Status.FAILED
        payment.failure_reason = str(exc)
        payment.save(update_fields=["status", "failure_reason", "updated_at"])
        _release_slot_hold(payment.booking)
        return render(request, "content/payment_result.html", {"success": False, "booking": payment.booking, "error": str(exc)})

    from apps.realtime.tasks import broadcast_slot_update
    broadcast_slot_update(str(payment.booking.slot_id))

    return render(request, "content/payment_result.html", {"success": True, "booking": payment.booking})


def _release_slot_hold(booking):
    slot = booking.slot
    if not slot.is_recurring_hold:
        slot.release_hold()
    booking.status = Booking.Status.AWAITING_PAYMENT
    booking.save(update_fields=["status", "updated_at"])
