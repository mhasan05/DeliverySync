# # chat/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import ChatRoom
from .serializers import ChatRoomSerializer, ChatMessageSerializer
from django.conf import settings
from accounts.models import User  # Assuming you have a User model in accounts app
from django.db.models import Q

class ChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all chat rooms the current user is part of.
        """
        rooms = ChatRoom.objects.filter(user1=request.user) | ChatRoom.objects.filter(user2=request.user)
        if rooms.exists():
            serializer = ChatRoomSerializer(rooms, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"message": "No chat rooms found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        """
        Create a chat room between two users.
        """
        user1 = request.user
        user2_id = request.data.get('user2')

        if not user2_id:
            return Response({"error": "user2 is required"}, status=status.HTTP_400_BAD_REQUEST)

        if user1.id == int(user2_id):
            return Response({"error": "You cannot create a room with yourself"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            return Response({"error": "User2 not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if room exists for either user order
        room = ChatRoom.objects.filter(
            (Q(user1=user1) & Q(user2=user2)) | (Q(user1=user2) & Q(user2=user1))
        ).first()

        if room:
            created = False
        else:
            room = ChatRoom.objects.create(user1=user1, user2=user2)
            created = True

        serializer = ChatRoomSerializer(room, context={'request': request})

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)


class ChatMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        """
        Get all messages in a chat room.
        """
        room = ChatRoom.objects.filter(Q(room_id=room_id) & (Q(user1=request.user) | Q(user2=request.user))).first()
        if room:
            for message in room.messages.filter(is_seen=False):
                message.is_seen = True
                message.save()  # Mark messages as seen
            serializer = ChatMessageSerializer(room.messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Chat room not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, room_id):
        """
        Send a message to a chat room.
        """
        try:
            room = ChatRoom.objects.get(room_id=room_id)
            data = {
                "room": room.room_id,
                "sender": request.user.id,
                "content": request.data.get("content")
            }
            serializer = ChatMessageSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found"}, status=status.HTTP_404_NOT_FOUND)
