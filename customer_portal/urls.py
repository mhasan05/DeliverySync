from django.urls import path
from .views import *
from driver_portal.views import *

urlpatterns = [
    path('delivery/create/', CreateDeliveryRequestView.as_view(), name='create-delivery'),
    path('delivery/cancel/<int:delivery_id>/', CancelDeliveryRequestView.as_view(), name='cancel-delivery'),
    path('delivery/accept/<int:delivery_id>/', AcceptDeliveryRequestView.as_view(), name='accept-delivery'),
    path('delivery/update/<int:delivery_id>/', UpdateDeliveryStatus.as_view(), name='update-delivery'),

    path('delivery/confirm/<int:delivery_id>/', ConfirmDelivery.as_view(), name='update-delivery'),

    path('delivery/rate/<str:delivery_id>/', RateDriverView.as_view(), name='rate-driver'),
    

    path('delivery/customer/', CustomerOrderListView.as_view(), name='customer-orders'),
    path('delivery/driver/', DriverOrderListView.as_view(), name='driver-orders'),
    path('delivery/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('delivery/pending_order/', PendingOrderListView.as_view(), name='pending_order'),
]
