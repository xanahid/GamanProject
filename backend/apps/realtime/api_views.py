from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scheduling.models import PushSubscription


class PushSubscribeView(APIView):
    """
    POST /api/v1/scheduling/push/subscribe/
    Body: {endpoint, keys: {p256dh, auth}}

    Called from the browser right after the user grants Notification
    permission (handled client-side by the React schedule widget's
    "notify me when free" toggle) and the Service Worker registers a
    PushSubscription via the browser's Push API.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get("endpoint")
        keys = request.data.get("keys", {})
        if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
            return Response({"detail": "اطلاعات اشتراک نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST)

        PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={"user": request.user, "p256dh": keys["p256dh"], "auth": keys["auth"]},
        )
        return Response({"status": "subscribed"}, status=status.HTTP_201_CREATED)


class PushUnsubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get("endpoint")
        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return Response({"status": "unsubscribed"})
