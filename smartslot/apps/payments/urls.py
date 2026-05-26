from django.urls import path
from .views import (
    payment_webhook, payment_callback, payment_return,
    mobile_money_operators, mobile_money_charge, mobile_money_status,
    momo_pay, cancel_pending_booking,
)

urlpatterns = [
    path('webhook/',                              payment_webhook,         name='payment_webhook'),
    path('callback/',                             payment_callback,        name='payment_callback'),
    path('return/',                               payment_return,          name='payment_return'),
    path('momo/operators/',                       mobile_money_operators,  name='momo_operators'),
    path('momo/charge/<int:booking_id>/',         mobile_money_charge,     name='momo_charge'),
    path('momo/status/<int:booking_id>/',         mobile_money_status,     name='momo_status'),
    path('momo/pay/<int:booking_id>/',            momo_pay,                name='momo_pay'),
    path('momo/cancel/<int:booking_id>/',         cancel_pending_booking,  name='momo_cancel'),
]
