from django.urls import path
from .views import BookingListView, internal_booking_view, external_booking_view, booking_pdf_view, cancel_booking_view, refund_policy_view

urlpatterns = [
    path('', BookingListView.as_view(), name='booking_list'),
    path('create/internal/<int:resource_pk>/', internal_booking_view,  name='booking_create_internal'),
    path('create/external/<int:resource_pk>/', external_booking_view,  name='booking_create_external'),
    path('<int:booking_id>/receipt/', booking_pdf_view, name='booking_receipt_pdf'),
    path('<int:booking_pk>/cancel/', cancel_booking_view, name='booking_cancel'),
    path('policy/refunds/', refund_policy_view, name='refund_policy'),
]

