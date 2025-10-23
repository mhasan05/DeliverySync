from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', UserDashboardView.as_view(), name='dashboard'),
]
