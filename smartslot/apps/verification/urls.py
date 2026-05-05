from django.urls import path
from .views import VerifyBookingView, CompleteBookingView, BookingDetailByTokenView

urlpatterns = [
    path('verify/', VerifyBookingView.as_view(), name='verify-booking'),
    path('complete/', CompleteBookingView.as_view(), name='complete-booking'),
    path('booking/', BookingDetailByTokenView.as_view(), name='booking-by-token'),
]
