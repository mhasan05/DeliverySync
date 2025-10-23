from rest_framework import serializers
from account.models import UserAuth


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        exclude = ['is_superuser', 'is_staff', 'groups', 'user_permissions','otp','otp_expired','is_active']
        extra_kwargs = {'password': {'write_only': True}}
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.role == "customer" or instance.role == "company":
            fields_to_remove = ["vehicle","vehicle_registration_number", "driving_license_number"]
            for field in fields_to_remove:
                representation.pop(field, None)

        return representation


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)



class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = ['new_password', 'confirm_password']


class ChangePasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        fields = ['old_password', 'new_password']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAuth
        exclude = ['password', 'is_superuser', 'is_staff', 'groups', 'user_permissions', 'otp', 'otp_expired', 'is_active','last_login']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Hide vehicle fields for non-drivers
        if instance.role != "driver":
            for field in ["vehicle", "vehicle_registration_number", "driving_license_number"]:
                representation.pop(field, None)
        return representation