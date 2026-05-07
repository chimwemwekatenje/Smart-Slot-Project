from django.urls import path
from .views import verify_booking_view

urlpatterns = [
    path('<str:qr_token>/', verify_booking_view, name='verify_booking'),
]
