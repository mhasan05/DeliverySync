# chat/urls.py

from django.urls import path
from .views import ChatRoomView, ChatMessageView

urlpatterns = [
    path('rooms/', ChatRoomView.as_view(), name='chat-room'),
    path('messages/<int:room_id>/', ChatMessageView.as_view(), name='chat-messages'),
]
