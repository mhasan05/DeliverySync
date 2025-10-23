from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from customer_portal.models import DeliveryRequest
from .models import *
from account.models import UserAuth
from .serializers import DriverRatingSerializer

class RateDriverView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, delivery_id):
        try:
            delivery = DeliveryRequest.objects.get(id=delivery_id)
        except DeliveryRequest.DoesNotExist:
            return Response({"status":"error","message": "Delivery not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure only the customer who made the delivery can rate
        if delivery.customer != request.user:
            return Response({"status":"error","message": "You are not allowed to rate this delivery."}, status=status.HTTP_403_FORBIDDEN)

        # Ensure the delivery has an assigned driver
        if not delivery.assign_driver:
            return Response({"status":"error","message": "No driver assigned for this delivery."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if rating already exists
        if hasattr(delivery, 'driver_rating'):
            return Response({"status":"error","message": "You have already rated this driver."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DriverRatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                delivery=delivery,
                driver=delivery.assign_driver,
                customer=request.user
            )
            return Response({"status":"success","message": "Driver rated successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
