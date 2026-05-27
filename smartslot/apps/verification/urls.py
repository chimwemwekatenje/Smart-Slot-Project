from django.urls import path
from .views import verify_booking_view, VerifyBookingView, CompleteBookingView, BookingDetailByTokenView

urlpatterns = [
    path('<str:qr_token>/', verify_booking_view, name='verify_booking'),
    path('verify/', VerifyBookingView.as_view(), name='verify-booking'),
    path('complete/', CompleteBookingView.as_view(), name='complete-booking'),
    path('booking/', BookingDetailByTokenView.as_view(), name='booking-by-token'),
]

