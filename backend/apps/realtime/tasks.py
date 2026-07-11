import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings


def broadcast_slot_update(slot_id):
    """
    Called synchronously from regular Django views/Celery tasks (booking
    creation, payment verification, cancellation, hold expiry) right after
    a SessionSlot's status changes, so every open schedule-grid browser
    tab updates live without polling.
    """
    from apps.scheduling.models import SessionSlot
    from apps.scheduling.serializers import SessionSlotSerializer

    try:
        slot = SessionSlot.objects.select_related("therapist").get(pk=slot_id)
    except SessionSlot.DoesNotExist:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    group_name = f"schedule_{slot.therapist_id}_{slot.date.isoformat()}"
    payload = SessionSlotSerializer(slot, context={"viewer_is_therapist": False}).data
    # Convert any non-JSON-serializable values (e.g. time objects) up front.
    payload = json.loads(json.dumps(payload, default=str))

    async_to_sync(channel_layer.group_send)(
        group_name, {"type": "slot.update", "slot": payload}
    )


def resolve_notify_requests_for_slot(slot_id):
    """
    When a slot transitions to free, check whether any client has an
    active NotifyRequest matching that therapist+weekday+time, and if so
    push them both an in-app notification (Channels) and a browser Web
    Push notification (works even with the tab closed, given granted
    permission).
    """
    from django.utils import timezone

    from apps.scheduling.models import NotifyRequest, SessionSlot, SLOT_STATUS_FREE

    try:
        slot = SessionSlot.objects.select_related("therapist__user").get(pk=slot_id)
    except SessionSlot.DoesNotExist:
        return

    if slot.status != SLOT_STATUS_FREE:
        return

    python_to_ours = {5: 0, 6: 1, 0: 2, 1: 3, 2: 4, 3: 5, 4: 6}
    weekday_choice = python_to_ours[slot.date.weekday()]

    matches = NotifyRequest.objects.filter(
        therapist=slot.therapist, weekday=weekday_choice, start_time=slot.start_time, is_active=True,
    ).select_related("client")

    channel_layer = get_channel_layer()
    for notify_req in matches:
        message = (
            f"یک نوبت با {slot.therapist.user.get_full_name()} در "
            f"{slot.date.isoformat()} ساعت {slot.start_time.strftime('%H:%M')} آزاد شد."
        )

        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                f"user_{notify_req.client_id}_notifications",
                {"type": "notify", "message": message, "data": {"slot_id": str(slot.id)}},
            )

        send_web_push_to_user(notify_req.client_id, message)

        notify_req.notified_at = timezone.now()
        notify_req.is_active = False  # one-shot; client can re-arm it
        notify_req.save(update_fields=["notified_at", "is_active"])


def send_web_push_to_user(user_id, message):
    """
    Fires a browser Web Push notification (visible even if no tab is open)
    to every device the user has granted notification permission on.
    Requires VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY to be configured — see
    README for `vapid_gen_keys` management command.
    """
    if not settings.VAPID_PRIVATE_KEY:
        return  # Web Push not configured in this environment; skip silently

    from pywebpush import WebPushException, webpush

    from apps.scheduling.models import PushSubscription

    for sub in PushSubscription.objects.filter(user_id=user_id):
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=json.dumps({"title": "گمان", "body": message}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
            )
        except WebPushException:
            # Subscription likely expired/revoked; drop it so we stop retrying.
            sub.delete()
