import json
import base64
import os
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from .models import ChatRoom, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        sender_id = data['sender']
        image_data = data.get('image')  # base64 image string or None

        message_obj = await self.save_message(self.room_id, sender_id, message, image_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_obj.content,
                'sender': sender_id,
                'image_url': message_obj.images.url if message_obj.images else None,
                'timestamp': str(message_obj.timestamp),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'image_url': event['image_url'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, room_id, sender_id, message, image_data):
        room = ChatRoom.objects.get(room_id=room_id)
        sender = User.objects.get(id=sender_id)
        image_file = None

        if image_data:
            # decode base64 and save
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{sender_id}.{ext}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'chat', filename)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(imgstr))

            image_file = f'chat/{filename}'  # relative path for ImageField

        return Message.objects.create(
            room=room,
            sender=sender,
            content=message,
            images=image_file if image_file else None
        )
