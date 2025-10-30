from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.contrib.auth import authenticate
from account.models import UserAuth
from account.serializers import *
from account.utils import generate_and_send_otp
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.base import ContentFile
import base64
import uuid
from django.db.models import Sum, Count
from datetime import timedelta
from customer_portal.models import DeliveryRequest as Order


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class RegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # --- Extract Fields ---
        name = serializer.validated_data.get('name')
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        role = serializer.validated_data.get('role')
        phone_number = serializer.validated_data.get('phone_number', '')
        address = serializer.validated_data.get('address', '')
        vehicle = serializer.validated_data.get('vehicle', '')
        vehicle_registration_number = serializer.validated_data.get('vehicle_registration_number', '')
        driving_license_number = serializer.validated_data.get('driving_license_number', '')

        # --- Handle Image ---
        image = None
        # 1️⃣ Multipart/form-data file
        if 'image' in request.FILES:
            image = request.FILES['image']
        # 2️⃣ Base64 string in JSON
        elif isinstance(serializer.validated_data.get('image'), str) and serializer.validated_data.get('image').startswith('data:image'):
            format, imgstr = serializer.validated_data.get('image').split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}")
        # 3️⃣ Default fallback
        else:
            image = 'profile_images/default.jpg'

        # --- Validation ---
        if UserAuth.objects.filter(email=email).exists():
            return Response({"status":"error","message":"Email already registered."}, status=400)
        if len(password) < 8:
            return Response({"status":"error","message":"Password must be at least 8 characters long."}, status=400)

        # --- Prepare user data ---
        user_data = {
            'email': email,
            'password': password,
            'name': name,
            'role': role,
            'phone_number': phone_number,
            'address': address,
            'image': image,
            'vehicle': vehicle,
            'vehicle_registration_number': vehicle_registration_number,
            'driving_license_number': driving_license_number
        }

        # Remove vehicle-related fields for customer/company
        if role in ['customer', 'company']:
            user_data.pop('vehicle')
            user_data.pop('vehicle_registration_number')
            user_data.pop('driving_license_number')

        # --- Create user ---
        user = UserAuth.objects.create_user(**user_data)
        user.is_active = False
        user.save()

        # --- Send OTP ---
        generate_and_send_otp(user)

        return Response({"status":"success","message":"Registration successful. OTP sent to email."}, status=201)

class ResendOTPView(APIView):
    """
    Allows users to request a new OTP if the previous one expired or they didn’t receive it.
    """

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data.get('email')

        # --- Validate ---
        try:
            user = UserAuth.objects.get(email=email)
        except UserAuth.DoesNotExist:
            return Response({"status":"error","message": "User not found."}, status=status.HTTP_404_NOT_FOUND)


        # --- Generate new OTP ---
        generate_and_send_otp(user)

        return Response(
            {"status":"success","message": "A new OTP has been sent to your email."},
            status=status.HTTP_200_OK
        )

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data.get('email')
        otp = serializer.validated_data.get('otp')

        try:
            user = UserAuth.objects.get(email=email)
        except UserAuth.DoesNotExist:
            return Response({"status":"error","message": "User not found."}, status=404)

        if not user.otp or not user.otp_expired:
            return Response({"status":"error","message": "No OTP found. Please request again."}, status=400)
        if timezone.now() > user.otp_expired:
            return Response({"status":"error","message": "OTP expired. Please request a new one."}, status=400)
        if user.otp != otp:
            return Response({"status":"error","message": "Invalid OTP."}, status=400)

        user.is_active = True
        user.otp = None
        user.otp_expired = None
        user.save()
        tokens = get_tokens_for_user(user)
        return Response({"status":"success","message": "Account verified successfully.","access_token":tokens}, status=200)

class LoginView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')

        # --- Validation layer ---
        if not email or not password:
            return Response({"status":"error","message": "Email and password are required."}, status=400)

        user = authenticate(email=email, password=password)
        if not user:
            return Response({"status":"error","message": "Invalid email or password."}, status=400)
        if not user.is_active:
            return Response({"status":"error","message": "Account not verified. Please verify OTP."}, status=403)
        
        # Calculate the streak
        last_login_date = user.last_login_date
        today = timezone.now().date()

        # Check if the user is logging in on consecutive days
        if last_login_date:
            if last_login_date == today - timedelta(days=1):
                # Continuation of streak
                user.login_streak += 1
            else:
                # Break in streak, reset to 1
                user.login_streak = 1
        else:
            # First login
            user.login_streak = 1

        # Update the last login date
        user.last_login_date = today
        user.save()

        tokens = get_tokens_for_user(user)
        if user.role == "driver":
            data = {"id": user.id,"name": user.name, "email": user.email, "image": user.image.url, "role": user.role, "phone_number": user.phone_number, "account_balance": user.account_balance, "address": user.address, "vehicle": user.vehicle, "vehicle_registration_number": user.vehicle_registration_number, "driving_license_number": user.driving_license_number}
        else:
            data = {"id": user.id,"name": user.name, "email": user.email, "image": user.image.url, "role": user.role, "phone_number": user.phone_number, "account_balance": user.account_balance, "address": user.address}
        return Response({
            "status":"success",
            "message": "Login successful.",
            "access_token": tokens,
            "data": data
        }, status=200)

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data.get('email')
        try:
            user = UserAuth.objects.get(email=email)
        except UserAuth.DoesNotExist:
            return Response({"status":"error","message": "User not found."}, status=404)

        generate_and_send_otp(user)
        return Response({"status":"success","message": "OTP sent to your email for password reset."}, status=200)

class ResetPasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # --- Validation layer ---
        if not new_password or not confirm_password:
            return Response({"status":"error","message": "Both new and confirm passwords are required."}, status=400)
        if len(new_password) < 8:
            return Response({"status":"error","message": "New password must be at least 8 characters long."}, status=400)
        if confirm_password != new_password:
            return Response({"status":"error","message": "Password doesn't match."}, status=400)

        user = request.user
        
        user.set_password(new_password)
        user.save()
        return Response({"status":"success","message": "Password reset successfully."}, status=200)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # --- Validation layer ---
        if not old_password or not new_password:
            return Response({"status":"error","message": "Both old and new passwords are required."}, status=400)
        if len(new_password) < 8:
            return Response({"status":"error","message": "New password must be at least 8 characters long."}, status=400)
        if old_password == new_password:
            return Response({"status":"error","message": "New password cannot be same as old password."}, status=400)

        user = request.user
        if not user.check_password(old_password):
            return Response({"status":"error","message": "Old password is incorrect."}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"status":"success","message": "Password changed successfully."}, status=200)




class UserProfileView(APIView):
    """Get current logged-in user profile"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response({"status": "success", "data": serializer.data}, status=200)


class AllUserProfileView(APIView):
    """Get all user profiles"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        users = UserAuth.objects.all()
        serializer = UserProfileSerializer(users, many=True)
        return Response({"status": "success", "data": serializer.data}, status=200)


class SingleUserProfileView(APIView):
    """Get single user profile by ID"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, user_id):
        try:
            user = UserAuth.objects.get(id=user_id)
        except UserAuth.DoesNotExist:
            return Response({"status":"error","message":"User not found"}, status=404)
        serializer = UserProfileSerializer(user)
        return Response({"status": "success", "data": serializer.data}, status=200)


class UpdateUserProfileView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, user_id):
        try:
            user = UserAuth.objects.get(id=user_id)
        except UserAuth.DoesNotExist:
            return Response({"status":"error","message":"User not found"}, status=404)

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # --- Handle Image ---
        image = None
        if 'image' in request.FILES:
            image = request.FILES['image']
        elif isinstance(request.data.get('image'), str) and request.data.get('image').startswith('data:image'):
            format, imgstr = request.data.get('image').split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}")

        if image:
            user.image = image

        # Update other fields
        for field in ['name', 'phone_number', 'address', 'vehicle', 'vehicle_registration_number', 'driving_license_number','location_latitude','location_longitude','is_online']:
            if request.data.get(field) is not None:
                setattr(user, field, request.data.get(field))

        user.save()
        serializer = UserProfileSerializer(user)
        return Response({"status":"success","data": serializer.data}, status=200)


class DeleteUserView(APIView):
    """Delete user by ID"""
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, user_id):
        try:
            user = UserAuth.objects.get(id=user_id)
        except UserAuth.DoesNotExist:
            return Response({"status":"error","message":"User not found"}, status=404)
        user.delete()
        return Response({"status":"success","message":"User deleted successfully"}, status=200)
    




class UpdateSelfUserProfileView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        try:
            user = request.user
        except UserAuth.DoesNotExist:
            return Response({"status":"error","message":"User not found"}, status=404)

        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # --- Handle Image ---
        image = None
        if 'image' in request.FILES:
            image = request.FILES['image']
        elif isinstance(request.data.get('image'), str) and request.data.get('image').startswith('data:image'):
            format, imgstr = request.data.get('image').split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}")

        if image:
            user.image = image

        # Update other fields
        for field in ['name', 'phone_number', 'address', 'vehicle', 'vehicle_registration_number', 'driving_license_number','location_latitude','location_longitude']:
            if request.data.get(field) is not None:
                setattr(user, field, request.data.get(field))

        user.save()
        serializer = UserProfileSerializer(user)
        return Response({"status":"success","data": serializer.data}, status=200)



from django.db.models.functions import TruncMonth
class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # 1. Total Users
        total_users = UserAuth.objects.count()

        # 2. Total Earnings (sum of completed orders)
        total_earnings = Order.objects.filter(status="delivered").aggregate(total=Sum("delivery_fee"))["total"] or 0

        # 3. New Users (e.g., new users registered in the last 30 days)
        new_users = UserAuth.objects.filter(date_joined__gte=timezone.now() - timedelta(days=30)).count()

        # 4. User Growth (users registered per month for the past year)
        user_growth_data = UserAuth.objects.filter(date_joined__gte=timezone.now() - timedelta(days=365))
        # Using TruncMonth to group by month
        user_growth_monthly = user_growth_data.annotate(month=TruncMonth('date_joined')) \
                                            .values('month') \
                                            .annotate(count=Count('id')) \
                                            .order_by('month')

        user_growth = {entry['month'].strftime('%Y-%m'): entry['count'] for entry in user_growth_monthly}

        # Prepare the final response data
        data = {
            "total_users": total_users,
            "total_earnings": round(total_earnings, 2),
            "new_users": new_users,
            "user_growth": user_growth,
        }
        return Response({"status":"success","data": data}, status=200)