from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum
from datetime import date
from customer_portal.models import DeliveryRequest

class UserDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = date.today()

        if user.role == 'customer':
            todays_order = DeliveryRequest.objects.filter(
                customer=user, created_at__date=today).count()
            
            total_pending_order = DeliveryRequest.objects.filter(
                customer=user).exclude(status='delivered').count()
            
            total_completed_order = DeliveryRequest.objects.filter(
                customer=user, status='delivered').count()

            data = {
                'todays_order': todays_order,
                'total_pending_order': total_pending_order,
                'total_completed_order': total_completed_order
            }

        elif user.role == 'driver':
            total_earning = (
            DeliveryRequest.objects.filter(assign_driver=user, status="delivered")
            .aggregate(total=Sum("delivery_fee"))["total"] or 0
        )
            total_assigned_deliveries = DeliveryRequest.objects.filter(
                assign_driver=user).count()
            total_delivered = DeliveryRequest.objects.filter(
                assign_driver=user, status='delivered').count()
            total_pending_deliveries = DeliveryRequest.objects.filter(
                assign_driver=user
            ).exclude(status='delivered').count()


            data = {
                'total_earning': total_earning,
                'total_assigned_deliveries': total_assigned_deliveries,
                'total_pending_deliveries': total_pending_deliveries,
                'total_delivered': total_delivered
                
            }

        elif user.role == 'company':
            todays_order = DeliveryRequest.objects.filter(
                customer=user, created_at__date=today).exclude(status='draft').count()
            total_ongoing_order = DeliveryRequest.objects.filter(
                customer=user
            ).exclude(status='delivered').exclude(status='draft').count()
            total_complited_order = DeliveryRequest.objects.filter(
                customer=user, status='delivered').count()
            total_canceled_order = DeliveryRequest.objects.filter(
                customer=user, status='cancel').count()

            data = {
                'todays_order': todays_order,
                'total_ongoing_order': total_ongoing_order,
                'total_complited_order': total_complited_order,
                'total_canceled_order': total_canceled_order,
            }

        else:
            data = {'message': 'Role not recognized'}

        return Response({"status": "success", "data": data}, status=200)
