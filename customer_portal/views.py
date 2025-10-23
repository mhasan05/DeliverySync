from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import DeliveryRequest
from account.models import UserAuth
from .serializers import *

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
        serializer = DeliveryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Calculate delivery fee
        product_weight = request.data.get('product_weight', 0)
        fee = calculate_delivery_fee(customer, product_weight)

        delivery_request = DeliveryRequest.objects.create(
            customer=customer,
            order_id=request.data.get('order_id',''),
            company_name=request.data.get('company_name',''),
            description=request.data.get('description',''),
            product_weight=product_weight,
            product_amount=request.data.get('product_amount',''),
            pickup_location=request.data.get('pickup_location',''),
            delivery_location=request.data.get('delivery_location',''),
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
        serializer = DeliveryRequestUpdateSerializer(delivery)
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

        assign_driver_id = delivery.assign_driver
        if assign_driver_id != request.user:
            return Response({"status":"error","message":"You can't update this delivery"}, status=404)
        status_update = request.data.get('status', None)

        if status_update:
            if status_update not in ['pending','assigned','in_transit','delivered','cancelled']:
                return Response({"status":"error","message":"Invalid status value"}, status=400)
        delivery.status = status_update
        delivery.save()
        serializer = DeliveryRequestUpdateSerializer(delivery)
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



# 1️⃣ Customer order list
class CustomerOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        customer = request.user
        orders = DeliveryRequest.objects.filter(customer=customer)
        serializer = DeliveryRequestSerializer(orders, many=True)
        return Response({"status":"success","data":serializer.data}, status=200)

# 2️⃣ Driver order list
class DriverOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        driver = request.user
        orders = DeliveryRequest.objects.filter(assign_driver=driver)
        serializer = DeliveryRequestSerializer(orders, many=True)
        return Response({"status":"success","data":serializer.data}, status=200)

# 3️⃣ Order details
class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = DeliveryRequest.objects.get(id=order_id)
        except DeliveryRequest.DoesNotExist:
            return Response({"status":"error","message":"Order not found"}, status=404)

        # Optional: restrict access
        if request.user.role == "customer" and order.customer != request.user:
            return Response({"status":"error","message":"Not authorized"}, status=403)
        if request.user.role == "driver" and order.assign_driver != request.user:
            return Response({"status":"error","message":"Not authorized"}, status=403)

        serializer = DeliveryRequestSerializer(order)
        return Response({"status":"success","data":serializer.data}, status=200)
    

# 1️⃣ Customer order list
class PendingOrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = DeliveryRequest.objects.filter(status='confirmed')
        serializer = DeliveryRequestSerializer(orders, many=True)
        return Response({"status":"success","data":serializer.data}, status=200)