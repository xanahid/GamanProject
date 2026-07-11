import json

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ScheduleConsumer(AsyncJsonWebsocketConsumer):
    """
    ws://.../ws/schedule/<therapist_id>/<date>/

    One group per (therapist, date) pair. Whenever a slot's status changes
    (someone starts checkout, a hold expires, a payment confirms, a
    cancellation frees a slot), every browser currently looking at that
    day's grid gets a live patch instead of needing to poll or refresh.
    """

    async def connect(self):
        self.therapist_id = self.scope["url_route"]["kwargs"]["therapist_id"]
        self.date_str = self.scope["url_route"]["kwargs"]["date"]
        self.group_name = f"schedule_{self.therapist_id}_{self.date_str}"

        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def slot_update(self, event):
        """Handler for 'slot.update' group_send events — see tasks.py."""
        await self.send_json({"type": "slot_update", "slot": event["slot"]})


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    ws://.../ws/notifications/

    Per-user private channel. Used to push "the slot you asked about is now
    free" alerts in-app, in addition to a browser Web Push notification
    when the tab is closed (see push.py).
    """

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f"user_{user.id}_notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        await self.send_json({"type": "notification", "message": event["message"], "data": event.get("data", {})})
