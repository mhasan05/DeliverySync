# chat/urls.py

from django.urls import path
from .views import *

urlpatterns = [
    path('create/', CreateNotificationView.as_view(), name='create-notification'),
    path('list/', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', SingleNotificationView.as_view(), name='notification-detail'),
    path('mark_all_as_read/', MarkAsReadView.as_view(), name='mark_all_as_read'),
    path('mark_read/<int:pk>/', MarkAsReadView.as_view(), name='mark_read'),
]
