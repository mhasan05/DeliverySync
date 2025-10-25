from rest_framework import serializers
from .models import DeliveryRequest
from account.models import UserAuth
from common_portal.utils import calculate_distance_and_time


class DriverDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = ['id', 'name', 'email', 'image', 'phone_number','vehicle', 'average_rating','total_ratings','location_latitude','location_longitude']


class DeliveryRequestSerializer(serializers.ModelSerializer):
    assign_driver_details = DriverDetailsSerializer(source='assign_driver', read_only=True)
    customer_details = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()
    estimated_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryRequest
        fields = '__all__'
        read_only_fields = ['delivery_fee', 'customer', 'status', 'created_at', 'updated_at']

    def get_customer_details(self, obj):
        if obj.customer:
            return {
                "id": obj.customer.id,
                "name": obj.customer.name,
                "email": obj.customer.email,
                "phone_number": obj.customer.phone_number,
                "image": obj.customer.image.url if obj.customer.image else None,
                "role": obj.customer.role,
                "location_latitude": obj.customer.location_latitude,
                "location_longitude": obj.customer.location_longitude
            }
        return None

    def get_distance_km(self, obj):
        if obj.assign_driver and obj.customer:
            distance, _ = calculate_distance_and_time(
                obj.assign_driver.location_latitude,
                obj.assign_driver.location_longitude,
                obj.customer.location_latitude,
                obj.customer.location_longitude
            )
            return distance
        return None

    def get_estimated_time_minutes(self, obj):
        if obj.assign_driver and obj.customer:
            _, eta = calculate_distance_and_time(
                obj.assign_driver.location_latitude,
                obj.assign_driver.location_longitude,
                obj.customer.location_latitude,
                obj.customer.location_longitude
            )
            return eta
        return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # Driver details
        rep["assign_driver_details"] = (
            DriverDetailsSerializer(instance.assign_driver).data
            if instance.assign_driver else None
        )

        # Distance & ETA
        rep["distance_km"] = self.get_distance_km(instance)
        rep["estimated_time_minutes"] = self.get_estimated_time_minutes(instance)

        return rep


class DeliveryRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRequest
        fields = ['assign_driver', 'status']