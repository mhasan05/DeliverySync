from rest_framework import serializers
from driver_portal.models import *

class DriverRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverRating
        fields = ['rating', 'comment']

class DriverEarningHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverEarningHistory
        fields = ['id', 'driver', 'delivery', 'amount', 'created_at']