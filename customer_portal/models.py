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
    delivery_location = models.CharField(max_length=255, blank=True)
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
    expected_delivery_time = models.DateTimeField(blank=True, null=True)
    actual_delivery_time = models.DateTimeField(blank=True, null=True)
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