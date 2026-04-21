from django.urls import path
from .views import BookingListView, internal_booking_view, external_booking_view

urlpatterns = [
    path('', BookingListView.as_view(), name='booking_list'),
    path('create/internal/<int:resource_pk>/', internal_booking_view,  name='booking_create_internal'),
    path('create/external/<int:resource_pk>/', external_booking_view,  name='booking_create_external'),
]
