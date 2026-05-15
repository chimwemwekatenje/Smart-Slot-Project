"""PayChangu payment views for SmartSlot."""
import logging
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from apps.bookings.models import Booking
from .models import Payment
from .services import verify_payment, verify_webhook_signature

logger = logging.getLogger(__name__)


def _confirm_booking(booking, tx_ref):
    """Mark a booking as Paid and create/update the Payment record."""
    if booking.status != Booking.StatusChoices.PAID:
        booking.status = Booking.StatusChoices.PAID
        booking.custom_data['tx_ref'] = tx_ref
        booking.custom_data['payment_status'] = 'paid'
        # Use update() to skip full_clean overlap check on status change
        Booking.objects.filter(pk=booking.pk).update(
            status=Booking.StatusChoices.PAID,
            custom_data=booking.custom_data,
        )

    # Create a Payment record if one doesn't exist yet
    Payment.objects.get_or_create(
        booking=booking,
        paychangu_reference=tx_ref,
        defaults={
            'amount': booking.resource.price,
            'status': Payment.StatusChoices.SUCCESS,
        },
    )


def _booking_from_tx_ref(tx_ref):
    """Extract booking from tx_ref format SMARTSLOT-{id}-{random}."""
    try:
        parts = tx_ref.split('-')
        if len(parts) >= 2:
            return Booking.objects.filter(id=int(parts[1])).first()
    except (ValueError, IndexError):
        pass
    return None


# ── Webhook (IPN) ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def payment_webhook(request):
    """
    PayChangu calls this URL server-to-server after a payment event.
    URL: /payments/webhook/
    Add this as PAYCHANGU_CALLBACK_URL in your environment.
    """
    # Verify signature
    signature = request.headers.get('X-Paychangu-Signature', '')
    if not verify_webhook_signature(request.body, signature):
        logger.warning('PayChangu webhook: invalid signature')
        # Still return 200 to avoid PayChangu retrying indefinitely,
        # but log the failure for investigation.

    tx_ref = request.POST.get('tx_ref') or request.GET.get('tx_ref')
    status = request.POST.get('status') or request.GET.get('status')

    if not tx_ref:
        return HttpResponse('Missing tx_ref', status=400)

    try:
        transaction = verify_payment(tx_ref)
        if transaction.get('status') == 'successful':
            booking = _booking_from_tx_ref(tx_ref)
            if booking:
                _confirm_booking(booking, tx_ref)
                logger.info(f'Booking {booking.id} confirmed via webhook.')
            else:
                logger.warning(f'Webhook: no booking found for tx_ref {tx_ref}')
    except Exception as e:
        logger.error(f'PayChangu webhook error: {e}')

    return HttpResponse('OK', status=200)


# ── Callback (legacy / redirect fallback) ────────────────────────────────────

@csrf_exempt
def payment_callback(request):
    """
    Fallback callback — handles both GET redirects and POST IPN calls.
    URL: /payments/callback/
    """
    tx_ref = request.GET.get('tx_ref') or request.POST.get('tx_ref')

    if not tx_ref:
        return HttpResponse('Missing tx_ref', status=400)

    try:
        transaction = verify_payment(tx_ref)
        if transaction.get('status') == 'successful':
            booking = _booking_from_tx_ref(tx_ref)
            if booking:
                _confirm_booking(booking, tx_ref)
    except Exception as e:
        logger.error(f'PayChangu callback error: {e}')

    return HttpResponse('OK', status=200)


# ── Return (user redirect after payment) ─────────────────────────────────────

def payment_return(request):
    """
    User lands here after completing or cancelling payment on PayChangu.
    URL: /payments/return/
    """
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')

    if status == 'failed' or not tx_ref:
        return render(request, 'payments/payment_failed.html')

    try:
        transaction = verify_payment(tx_ref)

        if transaction.get('status') == 'successful':
            booking = _booking_from_tx_ref(tx_ref)

            if booking:
                # Confirm in case webhook hasn't fired yet
                _confirm_booking(booking, tx_ref)

                from apps.bookings.views import _receipt_rows
                return render(request, 'bookings/booking_receipt.html', {
                    'booking':      booking,
                    'receipt_rows': _receipt_rows(booking),
                })

    except Exception as e:
        logger.error(f'PayChangu return error: {e}')

    return render(request, 'payments/payment_failed.html')
