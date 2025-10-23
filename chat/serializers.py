# chat/serializers.py

from rest_framework import serializers
from .models import *
from django.contrib.auth import get_user_model

User = get_user_model()

# serializers.py

class UserSummarySerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_picture']

    def get_profile_picture(self, obj):
        return obj.profile_picture.url if obj.profile_picture else None


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'room', 'sender', 'content', 'images','is_seen', 'timestamp']  # include 'room'


class ChatRoomSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unseen_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['room_id', 'user', 'last_message', 'unseen_count', 'created_at']

    def get_user(self, obj):
        request = self.context.get('request')
        if not request:
            return None

        if request.method == 'POST':
            # Get user2 ID from request data
            user2_id = request.data.get('user2')
            if user2_id:
                try:
                    user2 = User.objects.get(id=user2_id)
                    return UserSummarySerializer(user2).data
                except User.DoesNotExist:
                    return None
        else:
            # For GET: infer other user based on chat room participants
            current_user = request.user
            other_user = obj.user2 if obj.user1 == current_user else obj.user1
            return UserSummarySerializer(other_user).data

    def get_last_message(self, obj):
        last_msg = Message.objects.filter(room=obj).order_by('-timestamp').first()
        if last_msg:
            return {
                'content': last_msg.content,
                'timestamp': last_msg.timestamp,
                'sender_id': last_msg.sender.id,
            }
        return None

    def get_unseen_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Message.objects.filter(room=obj, is_seen=False).exclude(sender=request.user).count()
        return 0


