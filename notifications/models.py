from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    recipients = models.ManyToManyField(
        User,
        through='NotificationRecipient',
        related_name='notifications'
    )

    def __str__(self):
        return self.title

    def to_dict(self, user=None):
        """
        Optionally include read status for a specific user.
        """
        base = {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
        }
        if user:
            relation = NotificationRecipient.objects.filter(notification=self, recipient=user).first()
            base["is_read"] = relation.is_read if relation else False
        return base


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('notification', 'recipient')
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["notification"]),
        ]

    def __str__(self):
        return f"{self.recipient} - {self.notification.title}"
