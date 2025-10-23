from django.utils import timezone
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification, NotificationRecipient

User = get_user_model()
channel_layer = get_channel_layer()

def create_notification(title, message, data=None, recipient_ids=None, send_to_all=False):
    data = data or {}

    notification = Notification.objects.create(
        title=title,
        message=message,
        data=data,
        created_at=timezone.now()
    )

    if send_to_all:
        users = User.objects.all()
    elif isinstance(recipient_ids, int):
        users = User.objects.filter(id=recipient_ids)
    elif isinstance(recipient_ids, (list, tuple)):
        users = User.objects.filter(id__in=recipient_ids)
    else:
        raise ValueError("Provide recipient_ids (int/list) or set send_to_all=True")

    relations = [
        NotificationRecipient(notification=notification, recipient=user)
        for user in users
    ]
    NotificationRecipient.objects.bulk_create(relations)

    # 🔔 Send to WebSocket for real-time updates
    for user in users:
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}_notifications",
            {
                "type": "send_notification",
                "title": title,
                "message": message,
                "data": data,
                "created_at": notification.created_at.isoformat(),
            }
        )

    return notification
