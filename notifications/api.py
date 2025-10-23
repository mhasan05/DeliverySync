from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import NotificationSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class NotificationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notif = serializer.save(user=request.user)

        # broadcast to the user's websocket group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{notif.user_id}",
            {
                "type": "notification.message",
                "data": NotificationSerializer(notif).data,
            },
        )
        return Response(serializer.data)
