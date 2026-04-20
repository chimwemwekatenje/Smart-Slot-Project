from django.urls import path
from .views import BookingListView, internal_booking_view, external_booking_view

urlpatterns = [
    path('', BookingListView.as_view(), name='booking_list'),
    # resource_id is now a Firestore document ID (string), not a Django int PK
    path('create/internal/<str:resource_id>/', internal_booking_view,  name='booking_create_internal'),
    path('create/external/<str:resource_id>/', external_booking_view,  name='booking_create_external'),
]
