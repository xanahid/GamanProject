import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    """
    One row per payment attempt against a Booking. We store ZarinPal's
    `authority` (the transaction handle) and, on success, its `ref_id`
    (the settlement reference) — never card numbers, CVV2, or expiry,
    which only ever exist inside ZarinPal's hosted payment page per PCI-DSS
    scope reduction. `SavedCard.gateway_token` (accounts app) is the only
    thing that lets us pre-fill a saved card at the gateway, and even that
    is an opaque token ZarinPal gives us — not the PAN itself.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار"
        SUCCESS = "success", "موفق"
        FAILED = "failed", "ناموفق"
        REFUND_REQUESTED = "refund_requested", "در انتظار بازگشت وجه"
        REFUNDED = "refunded", "بازگشت داده‌شده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        "scheduling.Booking", on_delete=models.CASCADE, related_name="payments"
    )
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    amount_rials = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    gateway = models.CharField(max_length=30, default="zarinpal")
    authority = models.CharField(max_length=64, blank=True, db_index=True)
    ref_id = models.CharField(max_length=64, blank=True)
    card_pan_masked = models.CharField(max_length=25, blank=True, help_text="فقط نسخه ماسک‌شده — از پاسخ درگاه")
    saved_card_used = models.ForeignKey(
        "accounts.SavedCard", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )

    failure_reason = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"پرداخت {self.amount_rials} ریال — {self.get_status_display()}"


class RefundRequest(TimeStampedModel):
    """
    ZarinPal doesn't expose a universal instant-refund API for every
    merchant tier, so refunds are tracked here and settled by an
    operations/finance task (automatic where the gateway allows reversal,
    manual settlement queue otherwise) rather than assumed instant.
    """

    class Reason(models.TextChoices):
        CLIENT_CANCELLED_IN_TIME = "client_cancelled_in_time", "لغو به‌موقع توسط مراجع"
        THERAPIST_CANCELLED = "therapist_cancelled", "لغو توسط درمانگر"

    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="refund_request")
    reason = models.CharField(max_length=40, choices=Reason.choices)
    amount_rials = models.PositiveBigIntegerField()
    is_settled = models.BooleanField(default=False)
    settled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"بازگشت وجه {self.amount_rials} ریال — {'تسویه‌شده' if self.is_settled else 'در انتظار'}"
