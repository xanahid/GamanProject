from datetime import timedelta

from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import (
    RecurringBooking,
    SessionSlot,
    SLOT_STATUS_FREE,
    SLOT_STATUS_PENDING,
    WeeklyAvailability,
)

SLOT_GENERATION_HORIZON_DAYS = 60


@shared_task
def generate_upcoming_slots():
    """
    Run nightly. Walks every therapist's WeeklyAvailability templates and
    makes sure concrete SessionSlot rows exist for the next 60 days, in
    50-minute increments, so the schedule grid is always bookable that far
    ahead without anyone having to manually create rows.
    """
    today = timezone.localdate()
    horizon = today + timedelta(days=SLOT_GENERATION_HORIZON_DAYS)

    templates = WeeklyAvailability.objects.filter(is_active=True).select_related("therapist")
    created = 0

    for template in templates:
        day = today
        while day <= horizon:
            if day.weekday() == _normalize_weekday(template.weekday):
                created += _generate_day_slots(template, day)
            day += timedelta(days=1)

    return f"{created} slots created"


def _normalize_weekday(weekday_choice):
    # Our WEEKDAY_CHOICES uses 0=Saturday (Iranian week start); Python's
    # date.weekday() uses 0=Monday. Convert: Sat=5 in Python -> 0 for us.
    python_to_ours = {5: 0, 6: 1, 0: 2, 1: 3, 2: 4, 3: 5, 4: 6}
    inverse = {v: k for k, v in python_to_ours.items()}
    return inverse[weekday_choice]


def _generate_day_slots(template, day):
    from datetime import datetime, timedelta as td

    created = 0
    cursor = datetime.combine(day, template.start_time)
    end = datetime.combine(day, template.end_time)
    session_len = td(minutes=50)

    recurring_matches = RecurringBooking.objects.filter(
        therapist=template.therapist, weekday=template.weekday, is_active=True
    )

    while cursor + session_len <= end:
        start_t = cursor.time()
        end_t = (cursor + session_len).time()

        is_recurring = recurring_matches.filter(start_time=start_t).exists()
        try:
            with transaction.atomic():
                SessionSlot.objects.create(
                    therapist=template.therapist,
                    date=day,
                    start_time=start_t,
                    end_time=end_t,
                    status=SLOT_STATUS_PENDING if is_recurring else SLOT_STATUS_FREE,
                    is_recurring_hold=is_recurring,
                )
            created += 1
        except IntegrityError:
            pass  # slot already exists for this therapist/date/time — fine
        cursor += session_len

    return created


@shared_task
def release_expired_payment_holds():
    """
    Run every minute. Any SessionSlot stuck in pending_payment past its
    hold_expires_at (someone started checkout and abandoned it) goes back
    to free — unless it's a recurring soft-hold, which stays yellow.
    """
    now = timezone.now()
    stale = SessionSlot.objects.filter(status=SLOT_STATUS_PENDING, hold_expires_at__lt=now, is_recurring_hold=False)
    count = stale.count()
    for slot in stale:
        slot.release_hold()
        _notify_slot_freed.delay(str(slot.id))
    return f"{count} holds released"


@shared_task
def _notify_slot_freed(slot_id):
    """Fan-out to the realtime app: broadcast over Channels + resolve any matching NotifyRequest."""
    from apps.realtime.tasks import broadcast_slot_update, resolve_notify_requests_for_slot

    broadcast_slot_update(slot_id)
    resolve_notify_requests_for_slot(slot_id)
