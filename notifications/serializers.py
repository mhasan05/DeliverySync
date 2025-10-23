from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'body', 'is_read', 'created_at']
        read_only_fields = ['id', 'user', 'is_read', 'created_at']

    def create(self, validated_data):
        # Assign the user from context (DRF view)
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
