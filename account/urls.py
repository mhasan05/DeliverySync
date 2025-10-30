from django.urls import path
from account.views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),




    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profiles/', AllUserProfileView.as_view(), name='all-users'),
    path('profile/<int:user_id>/', SingleUserProfileView.as_view(), name='single-user'),
    path('profile/<int:user_id>/update/', UpdateUserProfileView.as_view(), name='update-user'),
    path('profile/update/', UpdateSelfUserProfileView.as_view(), name='profile_update'),
    path('profile/<int:user_id>/delete/', DeleteUserView.as_view(), name='delete-user'),

    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
]
