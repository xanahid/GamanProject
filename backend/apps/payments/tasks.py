from celery import shared_task

from .models import Payment, RefundRequest


@shared_task
def process_refund_for_booking(booking_id):
    """
    Queues a refund for a cancelled, paid booking. ZarinPal's standard
    merchant tier does not expose a guaranteed instant programmatic refund
    for every transaction, so we record a RefundRequest here for the
    finance/ops team to settle (bank transfer back to the same card, or
    ZarinPal's reversal API where eligible) rather than silently pretending
    money moved. This keeps the money-handling honest: status only flips to
    'refunded' once someone (or an automated settlement job, if/when
    Anthropic's — sorry, Gaman's — merchant tier supports it) confirms it.
    """
    from apps.scheduling.models import Booking

    try:
        booking = Booking.objects.select_related("slot").get(pk=booking_id)
    except Booking.DoesNotExist:
        return "booking not found"

    payment = Payment.objects.filter(booking=booking, status=Payment.Status.SUCCESS).order_by("-created_at").first()
    if payment is None:
        return "no successful payment to refund"

    reason = (
        RefundRequest.Reason.THERAPIST_CANCELLED
        if booking.status == Booking.Status.CANCELLED_BY_THERAPIST
        else RefundRequest.Reason.CLIENT_CANCELLED_IN_TIME
    )

    refund, _ = RefundRequest.objects.get_or_create(
        payment=payment,
        defaults={"reason": reason, "amount_rials": payment.amount_rials},
    )
    payment.status = Payment.Status.REFUND_REQUESTED
    payment.save(update_fields=["status", "updated_at"])

    return f"refund queued: {refund.id}"
