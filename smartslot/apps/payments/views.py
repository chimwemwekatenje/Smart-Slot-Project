from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from apps.bookings.models import Booking
from .services import verify_payment
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def payment_callback(request):
    """
    PayChangu calls this URL after a successful payment (IPN/webhook).
    We verify the transaction and confirm the booking.
    """
    tx_ref = request.GET.get('tx_ref') or request.POST.get('tx_ref')
    status = request.GET.get('status') or request.POST.get('status')

    if not tx_ref:
        return HttpResponse('Missing tx_ref', status=400)

    try:
        # Verify with PayChangu server-side
        transaction = verify_payment(tx_ref)

        if transaction.get('status') == 'successful':
            # Extract booking ID from tx_ref (SMARTSLOT-{id}-{random})
            parts = tx_ref.split('-')
            if len(parts) >= 2:
                booking_id = parts[1]
                booking = Booking.objects.filter(id=booking_id).first()
                if booking:
                    booking.status = Booking.StatusChoices.ISSUED
                    booking.custom_data['tx_ref'] = tx_ref
                    booking.custom_data['payment_status'] = 'paid'
                    booking.save()
                    logger.info(f"Booking {booking_id} confirmed via PayChangu.")

    except Exception as e:
        logger.error(f"PayChangu callback error: {e}")

    return HttpResponse('OK', status=200)


def payment_return(request):
    """
    User is redirected here after completing or cancelling payment.
    """
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')

    if status == 'failed' or not tx_ref:
        return render(request, 'payments/payment_failed.html')

    try:
        transaction = verify_payment(tx_ref)

        if transaction.get('status') == 'successful':
            # Find the booking
            parts = tx_ref.split('-')
            booking = None
            if len(parts) >= 2:
                booking = Booking.objects.filter(id=parts[1]).first()

            if booking:
                # Confirm booking if not already done by callback
                if booking.status == Booking.StatusChoices.PENDING:
                    booking.status = Booking.StatusChoices.ISSUED
                    booking.custom_data['tx_ref'] = tx_ref
                    booking.custom_data['payment_status'] = 'paid'
                    booking.save()

                from apps.bookings.views import _receipt_rows
                return render(request, 'bookings/booking_receipt.html', {
                    'booking': booking,
                    'receipt_rows': _receipt_rows(booking),
                })

    except Exception as e:
        logger.error(f"PayChangu return error: {e}")

    return render(request, 'payments/payment_failed.html')
