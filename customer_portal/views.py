from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import DeliveryRequest
from account.models import UserAuth
from .serializers import *
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from notifications.models import *
from common_portal.utils import calculate_distance_and_time
# Example delivery fee calculation function
def calculate_delivery_fee(customer, product_weight):
    base_fee = 50  # example base
    weight_factor = float(product_weight or 0) * 10
    # You can add customer-specific logic here
    return (customer.default_delivery_fee if hasattr(customer, 'default_delivery_fee') else 0) + base_fee + weight_factor


class CreateDeliveryRequestView(APIView):
    """Create new delivery request"""
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        customer = request.user
        data = request.data
        required_fields = ["pickup_location_lat", "pickup_location_long", "delivery_location_lat", "delivery_location_long"]
        if not all(field in data for field in required_fields):
            return Response({"status":"error","message":"Pickup and dropoff coordinates are required."}, status=400)
        pickup_location_lat = float(data["pickup_location_lat"])
        pickup_location_long = float(data["pickup_location_long"])
        delivery_location_lat = float(data["delivery_location_lat"])
        delivery_location_long = float(data["delivery_location_long"])

        distance_km, estimate_time = calculate_distance_and_time(pickup_location_lat, pickup_location_long, delivery_location_lat, delivery_location_long)
        default_delivery_fee = customer.default_delivery_fee if hasattr(customer, 'default_delivery_fee') else 0
        fee = distance_km * default_delivery_fee

        serializer = DeliveryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Calculate delivery fee
        product_weight = request.data.get('product_weight', 0)
        # fee = calculate_delivery_fee(customer, product_weight)

        delivery_request = DeliveryRequest.objects.create(
            customer=customer,
            order_id=request.data.get('order_id',''),
            company_name=request.data.get('company_name',''),
            description=request.data.get('description',''),
            product_weight=product_weight,
            product_amount=request.data.get('product_amount',''),
            pickup_location=request.data.get('pickup_location',''),
            pickup_location_lat=request.data.get('pickup_location_lat',''),
            pickup_location_long=request.data.get('pickup_location_long',''),
            delivery_location=request.data.get('delivery_location',''),
            delivery_location_lat=request.data.get('delivery_location_lat',''),
            delivery_location_long=request.data.get('delivery_location_long',''),
            distance_km=distance_km,
            delivery_fee=fee,
            assign_driver=None
        )

        response_serializer = DeliveryRequestSerializer(delivery_request)
        return Response({"status":"success","data":response_serializer.data}, status=201)


class CancelDeliveryRequestView(APIView):
    """Cancel delivery request by ID"""
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, delivery_id):
        try:
            delivery = DeliveryRequest.objects.get(id=delivery_id)
        except DeliveryRequest.DoesNotExist:
            return Response({"status":"error","message":"Delivery request not found"}, status=404)

        if delivery.status in ['delivered', 'cancelled']:
            return Response({"status":"error","message":"Cannot cancel delivered or already cancelled request"}, status=400)
        
        if delivery.status == 'confirmed':
            return Response({"status":"error","message":"can't cancel confirmed order"}, status=404)

        delivery.status = 'cancelled'
        delivery.save()
        return Response({"status":"success","message":"Delivery request cancelled"}, status=200)
    


class AcceptDeliveryRequestView(APIView):
    """
    Assign a driver and/or update status for a delivery request
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, delivery_id):
        try:
            delivery = DeliveryRequest.objects.get(id=delivery_id)
        except DeliveryRequest.DoesNotExist:
            return Response({"status":"error","message":"Delivery request not found"}, status=404)
        
        if delivery.assign_driver:
            return Response({"status":"error","message":"Already assign a driver"}, status=404)

        assign_driver_id = request.user
        status_update = 'assigned'
        delivery.assign_driver = assign_driver_id
        delivery.status = status_update
        delivery.save()
        try:
            # ---- Create Notification ----
            title = "Assign Driver"
            message = f"{request.user.name} accept your order."
            data = {"order_id": delivery.id}

            notification = Notification.objects.create(
                title=title,
                message=message,
                data=data,
                created_at=timezone.now()
            )

            invited_user = get_object_or_404(User, id=delivery.customer.id)

            # Create NotificationRecipient link
            NotificationRecipient.objects.create(
                notification=notification,
                recipient=invited_user
            )
            # ---- Push to WebSocket ----
            channel_layer = get_channel_layer()
            group_name = f"user_{invited_user.id}_notifications"

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",  # must match consumer method
                    "title": title,
                    "message": message,
                    "data": data,
                    "created_at": notification.created_at.isoformat(),
                }
            )
        except:
            pass
        return Response({"status":"success","message":"Successfully accept order"}, status=200)
    


class UpdateDeliveryStatus(APIView):
    """
    Assign a driver and/or update status for a delivery request
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, delivery_id):
        try:
            delivery = DeliveryRequest.objects.get(id=delivery_id)
        except DeliveryRequest.DoesNotExist:
            return Response({"status":"error","message":"Delivery request not found"}, status=404)
        if delivery.status == 'confirmed':
            return Response({"status":"error","message":"This order already confirmed"}, status=404)
        assign_driver_id = delivery.assign_driver
        if assign_driver_id != request.user:
            return Response({"status":"error","message":"You can't update this delivery"}, status=404)
        status_update = request.data.get('status', None)

        if status_update:
            if status_update not in ['pending','confirmed','assigned','picked_up','on_the_way','delivered','cancelled']:
                return Response({"status":"error","message":"Invalid status value"}, status=400)
        delivery.status = status_update
        delivery.save()
        try:
            # ---- Create Notification ----
            title = "Oder Update"
            if status_update == 'picked_up':
                message = f"A driver picked your parcel"
            elif status_update == 'on_the_way':
                message = f"A driver on the way with your parcel"
            elif status_update == 'delivered':
                message = f"your order mark as deliverd"
            data = {"order_id": delivery.id}

            notification = Notification.objects.create(
                title=title,
                message=message,
                data=data,
                created_at=timezone.now()
            )

            invited_user = get_object_or_404(User, id=delivery.customer.id)

            # Create NotificationRecipient link
            NotificationRecipient.objects.create(
                notification=notification,
                recipient=invited_user
            )
            # ---- Push to WebSocket ----
            channel_layer = get_channel_layer()
            group_name = f"user_{invited_user.id}_notifications"

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_notification",  # must match consumer method
                    "title": title,
                    "message": message,
                    "data": data,
                    "created_at": notification.created_at.isoformat(),
                }
            )
        except:
            pass
        return Response({"status":"success","message":"Successfully Update order"}, status=200)
    


class ConfirmDelivery(APIView):
    """
    Assign a driver and/or update status for a delivery request
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, delivery_id):
        try:
            delivery = DeliveryRequest.objects.get(id=delivery_id)
        except DeliveryRequest.DoesNotExist:
            return Response({"status":"error","message":"Delivery request not found"}, status=404)
        if delivery.status == 'confirmed':
            return Response({"status":"error","message":"This order already confirmed"}, status=404)
        customer = delivery.customer
        if customer != request.user:
            return Response({"status":"error","message":"You can't confirm this delivery"}, status=404)
        delivery.status = 'confirmed'
        delivery.save()
        return Response({"status":"success","message":"Successfully confirmed order"}, status=200)



# Customer order list
class CustomerOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        customer = request.user
        orders = DeliveryRequest.objects.filter(customer=customer)
        serializer = DeliveryRequestSerializer(orders, many=True)
        return Response({"status":"success","data":serializer.data}, status=200)

# Driver order list
class DriverOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        driver = request.user
        orders = DeliveryRequest.objects.filter(assign_driver=driver)
        serializer = DeliveryRequestSerializer(orders, many=True)
        return Response({"status":"success","data":serializer.data}, status=200)

# Order details
class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = DeliveryRequest.objects.get(id=order_id)
        except DeliveryRequest.DoesNotExist:
            return Response({"status":"error","message":"Order not found"}, status=404)

        # Optional: restrict access
        # if (request.user.role == "customer" or request.user.role == "company") and order.customer != request.user:
        #     return Response({"status":"error","message":"Not authorized"}, status=403)
        # if request.user.role == "driver" and order.assign_driver != request.user:
        #     return Response({"status":"error","message":"Not authorized"}, status=403)

        serializer = DeliveryRequestSerializer(order)
        return Response({"status":"success","data":serializer.data}, status=200)
    

# Pending order list
class PendingOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = DeliveryRequest.objects.filter(status='confirmed')
        serializer = DeliveryRequestSerializer(orders, many=True)
        return Response({"status":"success","data":serializer.data}, status=200)