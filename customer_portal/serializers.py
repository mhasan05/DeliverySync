from rest_framework import serializers
from .models import DeliveryRequest
from account.models import UserAuth


class DriverDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = ['id', 'name', 'email', 'image', 'phone_number','vehicle', 'average_rating','total_ratings']
        # If you added a rating field in UserAuth, include it here:
        # fields = ['id', 'name', 'email', 'image', 'phone_number', 'role', 'rating']


class DeliveryRequestSerializer(serializers.ModelSerializer):
    assign_driver_details = DriverDetailsSerializer(source='assign_driver', read_only=True)
    customer_details = serializers.SerializerMethodField()

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
                "role": obj.customer.role
            }
        return None

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        # Add readable driver details when assigned
        if instance.assign_driver:
            rep["assign_driver_details"] = DriverDetailsSerializer(instance.assign_driver).data
        else:
            rep["assign_driver_details"] = None

        return rep


class DeliveryRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRequest
        fields = ['assign_driver', 'status']