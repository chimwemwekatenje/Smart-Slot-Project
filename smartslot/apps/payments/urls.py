from django.urls import path
from .views import payment_callback, payment_return

urlpatterns = [
    path('callback/', payment_callback, name='payment_callback'),
    path('return/', payment_return, name='payment_return'),
]
