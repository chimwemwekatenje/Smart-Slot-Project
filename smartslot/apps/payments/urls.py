from django.urls import path
from .views import payment_webhook, payment_callback, payment_return

urlpatterns = [
    path('webhook/',  payment_webhook,  name='payment_webhook'),   # server-to-server IPN
    path('callback/', payment_callback, name='payment_callback'),  # legacy fallback
    path('return/',   payment_return,   name='payment_return'),    # user redirect
]
