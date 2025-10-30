from django.db import models
from account.models import UserAuth
from customer_portal.models import DeliveryRequest
from django.db.models import Avg, Count

class DriverRating(models.Model):
    delivery = models.OneToOneField(
        DeliveryRequest, on_delete=models.CASCADE, related_name="driver_rating"
    )
    driver = models.ForeignKey(
        UserAuth, on_delete=models.CASCADE, related_name="ratings_received"
    )
    customer = models.ForeignKey(
        UserAuth, on_delete=models.CASCADE, related_name="ratings_given"
    )
    rating = models.DecimalField(max_digits=3, decimal_places=2)  # e.g., 4.50
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Save the rating first
        super().save(*args, **kwargs)
        
        # Update driver's average_rating and total_ratings
        agg = DriverRating.objects.filter(driver=self.driver).aggregate(
            average=Avg('rating'),
            total=Count('id')
        )
        self.driver.average_rating = round(agg['average'] or 0, 2)
        self.driver.total_ratings = agg['total'] or 0
        self.driver.save()

    def __str__(self):
        return f"Rating {self.rating} for {self.driver.name} by {self.customer.name}"
    
class DriverEarningHistory(models.Model):
    driver = models.ForeignKey(UserAuth, on_delete=models.CASCADE)
    delivery = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver.name} earned {self.amount} for delivery {self.delivery.id}"
