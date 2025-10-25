from django.db import models
from account.models import UserAuth
from django.utils import timezone
import random

def generate_unique_id():
    """
    Generates a unique 6-digit ID.
    Retries until a unique ID is found in the DeliveryRequest table.
    """
    while True:
        rand_id = f"{random.randint(100000, 999999)}"  # 6 digits
        if not DeliveryRequest.objects.filter(id=rand_id).exists():
            return rand_id

class DeliveryRequest(models.Model):
    id = models.CharField(max_length=6, primary_key=True, editable=False)
    customer = models.ForeignKey(
        UserAuth, on_delete=models.CASCADE, related_name="delivery_requests"
    )
    order_id = models.CharField(max_length=255, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    product_weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    product_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    pickup_location = models.CharField(max_length=255, blank=True)
    pickup_location_lat = models.CharField(max_length=255,blank=True) #example = 22.379916347385546
    pickup_location_long = models.CharField(max_length=255,blank=True) #example = 91.8307064358106
    delivery_location = models.CharField(max_length=255, blank=True)
    delivery_location_lat = models.CharField(max_length=255,blank=True) #example = 22.379916347385546
    delivery_location_long = models.CharField(max_length=255,blank=True) #example = 91.8307064358106
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    assign_driver = models.ForeignKey(
        UserAuth, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_deliveries"
    )
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('assigned', 'Assigned'),
            ('picked_up', 'Picked Up'),
            ('on_the_way', 'On The Way'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_unique_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"DeliveryRequest {self.order_id or 'N/A'} ({self.id}) by {self.customer.name}"


# class OrderTrack(models.Model):
#     delivery_request = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name="tracks")
#     status = models.CharField(
#         max_length=20,
#         choices=[
#             ('pending', 'Pending'),
#             ('assigned', 'Assigned'),
#             ('in_transit', 'In Transit'),
#             ('delivered', 'Delivered'),
#             ('cancelled', 'Cancelled')
#         ],
#         default='pending'
#     )
#     updated_by = models.ForeignKey(UserAuth, on_delete=models.SET_NULL, null=True, blank=True)
#     location = models.CharField(max_length=255, blank=True)  # optional: track current location
#     remark = models.TextField(blank=True)
#     created_at = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"{self.delivery_request.order_id} - {self.status}"