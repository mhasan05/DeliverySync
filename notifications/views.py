from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Notification, NotificationRecipient
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

User = get_user_model()


class CreateNotificationView(APIView):
    """
    Create a new notification for one user, multiple users, or all users.
    """
    permission_classes = [IsAuthenticated]  # restrict to admin

    def post(self, request):
        title = request.data.get("title")
        message = request.data.get("message")
        data = request.data.get("data", {})
        recipient_ids = request.data.get("recipient_ids", [])
        send_to_all = request.data.get("send_to_all", False)

        if not title or not message:
            return Response({"error": "title and message are required."}, status=400)

        # Create the main notification
        notification = Notification.objects.create(
            title=title,
            message=message,
            data=data,
            created_at=timezone.now()
        )

        # Select recipients
        if send_to_all:
            users = User.objects.all()
        elif isinstance(recipient_ids, list) and len(recipient_ids) > 0:
            users = User.objects.filter(id__in=recipient_ids)
        else:
            return Response({"error": "Provide recipient_ids or set send_to_all=True"}, status=400)

        # Create NotificationRecipient relations
        relations = [
            NotificationRecipient(notification=notification, recipient=user)
            for user in users
        ]
        NotificationRecipient.objects.bulk_create(relations)

        # ✅ Send WebSocket notification to each user
        channel_layer = get_channel_layer()
        for user in users:
            group_name = f"user_{user.id}_notifications"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",  # must match consumer method
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                }
            )

        return Response({
            "status": "success",
            "notification_id": notification.id,
            "recipients_count": len(relations)
        }, status=201)



class NotificationListView(APIView):
    """
    Get all notifications for the logged-in user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        relations = NotificationRecipient.objects.filter(
            recipient=user
        ).select_related("notification").order_by('-created_at')

        unread_count = relations.filter(is_read=False).count()

        data = [
            relation.notification.to_dict(user=user)
            for relation in relations
        ]

        return Response({
            "status": "success",
            "unread_count": unread_count,
            "data": data
        })


class MarkAsReadView(APIView):
    """
    Mark one notification or all notifications as read for the logged-in user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        user = request.user

        if pk:
            relation = get_object_or_404(NotificationRecipient, notification_id=pk, recipient=user)
            relation.is_read = True
            relation.save()
        else:
            NotificationRecipient.objects.filter(recipient=user, is_read=False).update(is_read=True)

        return Response({"status": "success"})


class SingleNotificationView(APIView):
    """
    Retrieve a single notification for the user and mark it as read.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        relation = get_object_or_404(NotificationRecipient, notification_id=pk, recipient=user)
        
        # Mark as read
        if not relation.is_read:
            relation.is_read = True
            relation.save()

        notification = relation.notification
        return Response({
            "status": "success",
            "data": notification.to_dict(user=user)
        })
