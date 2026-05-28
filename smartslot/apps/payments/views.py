"""PayChangu payment views for SmartSlot."""
import json
import logging
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from apps.bookings.models import Booking
from .models import Payment
from .services import (
    verify_payment, verify_webhook_signature,
    charge_mobile_money, get_charge_details, get_mobile_money_operators,
)

logger = logging.getLogger(__name__)


def _confirm_booking(booking, tx_ref):
    """Mark a booking as Booked and create/update the Payment record."""
    if booking.status != Booking.StatusChoices.BOOKED:
        Booking.objects.filter(pk=booking.pk).update(
            status=Booking.StatusChoices.BOOKED,
            custom_data={**booking.custom_data, 'tx_ref': tx_ref, 'payment_status': 'paid'},
        )
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


# ── Mobile Money operators (JSON) ─────────────────────────────────────────────

@require_GET
def mobile_money_operators(request):
    """Returns supported operators as JSON for the inline payment form."""
    try:
        operators = get_mobile_money_operators()
        return JsonResponse({'status': 'success', 'data': operators})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ── Mobile Money charge (inline, no redirect) ─────────────────────────────────

@login_required
@require_POST
def mobile_money_charge(request, booking_id):
    """
    Initiates a direct mobile money charge for a pending booking.
    Called via AJAX from the payment step.
    Returns JSON with charge_id for polling.
    """
    booking = Booking.objects.filter(id=booking_id, user=request.user).first()
    if not booking:
        return JsonResponse({'status': 'error', 'message': 'Booking not found.'}, status=404)

    if booking.status == Booking.StatusChoices.BOOKED:
        return JsonResponse({'status': 'already_paid'})

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        body = {}

    mobile_number   = body.get('mobile_number', '').strip()
    operator_ref_id = body.get('operator_ref_id', '').strip()

    if not mobile_number or not operator_ref_id:
        return JsonResponse({'status': 'error', 'message': 'Mobile number and operator are required.'}, status=400)

    user = request.user
    first_name = user.first_name or user.username
    last_name  = user.last_name or ''
    email      = user.email or ''

    try:
        charge_data = charge_mobile_money(
            booking=booking,
            mobile_number=mobile_number,
            operator_ref_id=operator_ref_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        # Log the full response so we can see what PayChangu returns
        logger.info(f'PayChangu charge response for booking {booking_id}: {charge_data}')

        tx_ref    = charge_data.get('tx_ref', '')
        # PayChangu returns their numeric charge_id in the response data
        charge_id = (
            charge_data.get('charge_id') or
            charge_data.get('chargeId') or
            charge_data.get('id') or
            tx_ref
        )
        booking.custom_data['charge_id'] = str(charge_id)
        booking.custom_data['tx_ref']    = tx_ref
        Booking.objects.filter(pk=booking.pk).update(custom_data=booking.custom_data)

        return JsonResponse({
            'status':    'pending',
            'charge_id': str(charge_id),
            'message':   'Payment request sent. Please check your phone and enter your PIN.',
        })
    except Exception as e:
        logger.error(f'Mobile money charge error: {e}')
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ── Poll charge status ────────────────────────────────────────────────────────

@login_required
@require_GET
def mobile_money_status(request, booking_id):
    """
    Polls the status of a mobile money charge.
    Called repeatedly by the frontend until success or failure.
    """
    booking = Booking.objects.filter(id=booking_id, user=request.user).first()
    if not booking:
        return JsonResponse({'status': 'error', 'message': 'Booking not found.'}, status=404)

    if booking.status == Booking.StatusChoices.BOOKED:
        return JsonResponse({'status': 'success', 'redirect': f'/bookings/'})

    charge_id = booking.custom_data.get('charge_id', '')
    tx_ref    = booking.custom_data.get('tx_ref', '')

    if not charge_id:
        return JsonResponse({'status': 'error', 'message': 'No charge in progress.'}, status=400)

    try:
        charge = get_charge_details(charge_id)
        logger.info(f'Charge status for booking {booking_id}: {charge}')
        charge_status = charge.get('status', '')

        if charge_status == 'success':
            _confirm_booking(booking, tx_ref)
            booking.refresh_from_db()
            return JsonResponse({'status': 'success', 'redirect': f'/payments/return/?tx_ref={tx_ref}'})
        elif charge_status in ('failed', 'cancelled'):
            # Cancel the pending booking so the slot is freed
            Booking.objects.filter(pk=booking.pk).update(
                status=Booking.StatusChoices.CANCELLED
            )
            return JsonResponse({'status': 'failed', 'message': 'Payment was not completed. Your booking has been cancelled.'})
        else:
            return JsonResponse({'status': 'pending', 'message': 'Waiting for payment confirmation...'})

    except Exception as e:
        logger.error(f'Mobile money status poll error for booking {booking_id}: {e}')
        # Don't return error to frontend — keep polling, the charge may still be processing
        return JsonResponse({'status': 'pending', 'message': 'Checking payment status...'})


# ── Webhook (IPN) ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def payment_webhook(request):
    """PayChangu server-to-server IPN. URL: /payments/webhook/"""
    signature = request.headers.get('X-Paychangu-Signature', '')
    if not verify_webhook_signature(request.body, signature):
        logger.warning('PayChangu webhook: invalid signature')

    # PayChangu sends JSON body
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        payload = {}

    logger.info(f'PayChangu webhook payload: {payload}')

    # tx_ref may be in body JSON or query params
    tx_ref = (
        payload.get('tx_ref') or
        payload.get('data', {}).get('tx_ref') or
        request.POST.get('tx_ref') or
        request.GET.get('tx_ref')
    )
    charge_id = (
        payload.get('charge_id') or
        payload.get('data', {}).get('charge_id') or
        payload.get('chargeId') or
        payload.get('data', {}).get('chargeId')
    )
    event_status = (
        payload.get('status') or
        payload.get('data', {}).get('status', '')
    )

    if not tx_ref and not charge_id:
        logger.warning('PayChangu webhook: no tx_ref or charge_id in payload')
        return HttpResponse('OK', status=200)

    try:
        # Check if this is an Organisation Application payment
        is_org_app = False
        app_id = None
        
        if tx_ref and tx_ref.startswith('ORGAPP-'):
            is_org_app = True
            try:
                app_id = int(tx_ref.split('-')[1])
            except (ValueError, IndexError):
                pass

        if event_status in ('successful', 'success'):
            if is_org_app and app_id:
                from apps.core.models import OrganisationApplication
                from apps.accounts.services import onboard_organisation
                app = OrganisationApplication.objects.filter(id=app_id).first()
                if app and app.status == OrganisationApplication.StatusChoices.APPROVED_FOR_PAYMENT:
                    app.status = OrganisationApplication.StatusChoices.PAID
                    app.save(update_fields=['status'])
                    onboard_organisation(app)
                    logger.info(f'Organisation Application {app_id} onboarded successfully via webhook.')
                return HttpResponse('OK', status=200)

            booking = None
            if tx_ref:
                booking = _booking_from_tx_ref(tx_ref)
            if not booking and charge_id:
                booking = Booking.objects.filter(
                    custom_data__charge_id=str(charge_id)
                ).first()
            if booking:
                _confirm_booking(booking, tx_ref or str(charge_id))
                logger.info(f'Booking {booking.id} confirmed via webhook.')
            else:
                logger.warning(f'Webhook: no booking found for tx_ref={tx_ref} charge_id={charge_id}')
        else:
            # Verify via API as fallback
            if tx_ref:
                transaction = verify_payment(tx_ref)
                if transaction.get('status') == 'successful':
                    if is_org_app and app_id:
                        from apps.core.models import OrganisationApplication
                        from apps.accounts.services import onboard_organisation
                        app = OrganisationApplication.objects.filter(id=app_id).first()
                        if app and app.status == OrganisationApplication.StatusChoices.APPROVED_FOR_PAYMENT:
                            app.status = OrganisationApplication.StatusChoices.PAID
                            app.save(update_fields=['status'])
                            onboard_organisation(app)
                            logger.info(f'Organisation Application {app_id} onboarded successfully via webhook verification.')
                        return HttpResponse('OK', status=200)

                    booking = _booking_from_tx_ref(tx_ref)
                    if booking:
                        _confirm_booking(booking, tx_ref)
                        logger.info(f'Booking {booking.id} confirmed via webhook verify.')
    except Exception as e:
        logger.error(f'PayChangu webhook error: {e}')

    return HttpResponse('OK', status=200)


# ── Callback (legacy fallback) ────────────────────────────────────────────────

@csrf_exempt
def payment_callback(request):
    """Fallback callback. URL: /payments/callback/"""
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
    """User lands here after PayChangu redirect. URL: /payments/return/"""
    tx_ref = request.GET.get('tx_ref')
    status = request.GET.get('status')

    if status == 'failed' or not tx_ref:
        return render(request, 'payments/payment_failed.html')

    try:
        transaction = verify_payment(tx_ref)
        if transaction.get('status') == 'successful':
            booking = _booking_from_tx_ref(tx_ref)
            if booking:
                _confirm_booking(booking, tx_ref)
                # Refresh from DB
                booking.refresh_from_db()
                from apps.bookings.views import _receipt_rows
                return render(request, 'bookings/booking_receipt.html', {
                    'booking':      booking,
                    'receipt_rows': _receipt_rows(booking),
                })
    except Exception as e:
        logger.error(f'PayChangu return error: {e}')

    return render(request, 'payments/payment_failed.html')



# ── Mobile Money payment page ─────────────────────────────────────────────────

@login_required
def momo_pay(request, booking_id):
    """
    Dedicated mobile money payment page shown after booking is created as Pending.
    User selects operator, enters phone, and we charge inline.
    URL: /payments/momo/pay/<booking_id>/
    """
    from django.shortcuts import get_object_or_404
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Already confirmed — show receipt
    if booking.status == Booking.StatusChoices.BOOKED:
        from apps.bookings.views import _receipt_rows
        return render(request, 'bookings/booking_receipt.html', {
            'booking':      booking,
            'receipt_rows': _receipt_rows(booking),
        })

    # Cancelled
    if booking.status == Booking.StatusChoices.CANCELLED:
        return render(request, 'payments/payment_failed.html')

    return render(request, 'payments/momo_pay.html', {'booking': booking})


# ── Cancel pending booking (payment timeout/failure) ─────────────────────────

@login_required
@require_POST
def cancel_pending_booking(request, booking_id):
    """Cancels a Pending booking when payment times out or fails."""
    from apps.bookings.models import Booking as B
    booking = B.objects.filter(id=booking_id, user=request.user).first()
    if booking and booking.status not in (B.StatusChoices.BOOKED,):
        B.objects.filter(pk=booking.pk).update(status=B.StatusChoices.CANCELLED)
    return JsonResponse({'status': 'cancelled'})
