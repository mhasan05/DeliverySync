from django.db import models
from account.models import UserAuth

class ChatRoom(models.Model):
    room_id = models.AutoField(primary_key=True)
    user1 = models.ForeignKey(UserAuth, on_delete=models.CASCADE, related_name='chat_user1')
    user2 = models.ForeignKey(UserAuth, on_delete=models.CASCADE, related_name='chat_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.room_id)

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(UserAuth, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    images = models.ImageField(upload_to='chat/', blank=True,default='')
    is_seen = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content}"

class MessageImage(models.Model):
    image = models.ImageField(upload_to='chat/images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
