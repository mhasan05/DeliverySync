from django.urls import path
from .views import *

urlpatterns = [
    path('earning_history/', DriverEarningHistoryView.as_view(), name='earning_history'),
    path('single_earning_history/<int:pk>/', DriverEarningHistoryView.as_view(), name='single_earning_history'),
]
