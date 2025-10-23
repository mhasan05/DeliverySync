from rest_framework import serializers
from driver_portal.models import DriverRating

class DriverRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverRating
        fields = ['rating', 'comment']
