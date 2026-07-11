import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

# ---------------------------------------------------------------------------
# Slot status — single source of truth driving BOTH color schemes:
#
#   Status            | Client sees | Therapist sees | Meaning
#   ------------------|-------------|-----------------|----------------------
#   free              | white       | white           | open, bookable
#   pending_payment   | yellow      | yellow          | someone is mid-checkout
#                      |             |                 | OR this is a client's
#                      |             |                 | weekly recurring slot
#                      |             |                 | that hasn't been paid
#                      |             |                 | for *this specific
#                      |             |                 | week* yet
#   booked            | red         | green           | paid & confirmed
#
# Same three states, just relabelled per audience — exactly matching the
# spec's white/yellow/red (client) vs white/yellow/green (therapist) tables.
# ---------------------------------------------------------------------------
SLOT_STATUS_FREE = "free"
SLOT_STATUS_PENDING = "pending_payment"
SLOT_STATUS_BOOKED = "booked"

SLOT_STATUS_CHOICES = [
    (SLOT_STATUS_FREE, "آزاد"),
    (SLOT_STATUS_PENDING, "در انتظار پرداخت"),
    (SLOT_STATUS_BOOKED, "رزرو و پرداخت‌شده"),
]


class WeeklyAvailability(TimeStampedModel):
    """
    Recurring weekly template a therapist sets up once (e.g. "available
    Tuesdays 09:00-17:00"). Actual bookable SessionSlot rows are generated
    from this template ahead of time by a Celery beat task (see tasks.py),
    so real slots always exist far enough in advance to book but the
    therapist only has to define their week shape once.
    """

    WEEKDAY_CHOICES = [
        (0, "شنبه"), (1, "یک‌شنبه"), (2, "دوشنبه"),
        (3, "سه‌شنبه"), (4, "چهارشنبه"), (5, "پنج‌شنبه"), (6, "جمعه"),
    ]

    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="weekly_availability"
    )
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name_plural = "Weekly availabilities"

    def __str__(self):
        return f"{self.therapist} — {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class SessionSlot(TimeStampedModel):
    """
    One concrete, bookable 50-minute block on a specific calendar date.
    This is what the day-based schedule grid (white/yellow/red|green) is
    built from, and what Booking + Payment point at.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="slots"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=SLOT_STATUS_CHOICES, default=SLOT_STATUS_FREE)

    # Set when a client toggles "make this a permanent weekly booking" —
    # this slot's *future* recurring siblings get pre-marked yellow even
    # before anyone starts a checkout, exactly per the spec.
    is_recurring_hold = models.BooleanField(default=False)
    recurring_booking = models.ForeignKey(
        "RecurringBooking", on_delete=models.SET_NULL, null=True, blank=True, related_name="generated_slots"
    )

    # Whoever currently holds this slot mid-checkout or has booked it.
    held_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="held_slots"
    )
    hold_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("therapist", "date", "start_time")
        indexes = [models.Index(fields=["therapist", "date"])]

    def __str__(self):
        return f"{self.therapist} {self.date} {self.start_time} [{self.status}]"

    @property
    def is_hold_expired(self):
        return (
            self.status == SLOT_STATUS_PENDING
            and self.hold_expires_at is not None
            and timezone.now() > self.hold_expires_at
            and not self.is_recurring_hold
        )

    def place_payment_hold(self, user):
        self.status = SLOT_STATUS_PENDING
        self.held_by = user
        self.hold_expires_at = timezone.now() + timedelta(
            minutes=getattr(settings, "SLOT_PAYMENT_HOLD_MINUTES", 15)
        )
        self.save(update_fields=["status", "held_by", "hold_expires_at", "updated_at"])

    def release_hold(self):
        if self.is_recurring_hold:
            # Recurring soft-holds revert to "pending" yellow forever (per
            # spec: it stays yellow until someone actually pays for that
            # specific week), not all the way back to free.
            self.status = SLOT_STATUS_PENDING
        else:
            self.status = SLOT_STATUS_FREE
        self.held_by = None
        self.hold_expires_at = None
        self.save(update_fields=["status", "held_by", "hold_expires_at", "updated_at"])

    def mark_booked(self, client):
        self.status = SLOT_STATUS_BOOKED
        self.held_by = client
        self.hold_expires_at = None
        self.save(update_fields=["status", "held_by", "hold_expires_at", "updated_at"])


class RecurringBooking(TimeStampedModel):
    """
    Represents a client's standing "same time every week" arrangement with
    a therapist. Doesn't book every future slot outright (that would lock
    money the client hasn't paid yet) — instead it just flags the matching
    weekly SessionSlots as is_recurring_hold=True/yellow, and the client
    still pays week-by-week like any other booking.
    """

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recurring_bookings")
    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="recurring_bookings"
    )
    weekday = models.PositiveSmallIntegerField(choices=WeeklyAvailability.WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("client", "therapist", "weekday", "start_time")

    def __str__(self):
        return f"{self.client} ⟷ {self.therapist} هر {self.get_weekday_display()} {self.start_time}"


class Booking(TimeStampedModel):
    """
    A confirmed (or being-confirmed) reservation tying a client to a slot.
    One-to-one with SessionSlot in practice (a slot only ever has one live
    booking), kept as its own model so SessionNote and Payment can point at
    something booking-shaped without overloading SessionSlot.
    """

    class Status(models.TextChoices):
        AWAITING_PAYMENT = "awaiting_payment", "در انتظار پرداخت"
        CONFIRMED = "confirmed", "تأیید شده"
        CANCELLED_BY_CLIENT = "cancelled_by_client", "لغو توسط مراجع"
        CANCELLED_BY_THERAPIST = "cancelled_by_therapist", "لغو توسط درمانگر"
        COMPLETED = "completed", "برگزار شده"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slot = models.OneToOneField(SessionSlot, on_delete=models.CASCADE, related_name="booking")
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="bookings"
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.AWAITING_PAYMENT)
    is_weekly_recurring = models.BooleanField(default=False)
    is_first_session = models.BooleanField(
        default=False, help_text="جلسه ارزیابی اولیه با دکتر اکبرزاده"
    )

    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    def __str__(self):
        return f"{self.client} → {self.therapist} @ {self.slot.date} {self.slot.start_time}"

    @property
    def session_datetime(self):
        return timezone.datetime.combine(self.slot.date, self.slot.start_time)

    @property
    def hours_until_session(self):
        now = timezone.now()
        session_dt = timezone.make_aware(self.session_datetime) if timezone.is_naive(self.session_datetime) else self.session_datetime
        return (session_dt - now).total_seconds() / 3600

    @property
    def client_can_get_refund_if_cancelled_now(self):
        return self.hours_until_session >= settings.CLIENT_CANCELLATION_WINDOW_HOURS


class NotifyRequest(TimeStampedModel):
    """
    "Notify me if this slot opens up" — a client can ask to be pushed a
    notification if a specific weekday+time with their therapist becomes
    free (e.g. someone else cancels). Resolved by a signal/task whenever a
    slot transitions to free; see realtime/tasks.py.
    """

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notify_requests")
    therapist = models.ForeignKey(
        "therapists.TherapistProfile", on_delete=models.CASCADE, related_name="notify_requests"
    )
    weekday = models.PositiveSmallIntegerField(choices=WeeklyAvailability.WEEKDAY_CHOICES)
    start_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("client", "therapist", "weekday", "start_time")

    def __str__(self):
        return f"اطلاع‌رسانی برای {self.client} — {self.therapist} {self.get_weekday_display()} {self.start_time}"


class PushSubscription(TimeStampedModel):
    """Browser Web Push subscription, one per device/browser the user granted permission on."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)

    def __str__(self):
        return f"Push subscription for {self.user}"
