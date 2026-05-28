import logging
from django.utils import timezone
from apps.bookings.models import Booking
from apps.payments.models import Payment
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def _cancel_booking_record(booking, cancellation_reason, payment_status):
    custom_data = {
        **(booking.custom_data or {}),
        'booking_status': 'cancelled',
        'cancelled_at': timezone.now().isoformat(),
        'cancellation_reason': cancellation_reason,
        'payment_status': payment_status,
    }
    Booking.objects.filter(pk=booking.pk).update(
        status=Booking.StatusChoices.CANCELLED,
        custom_data=custom_data,
    )
    booking.status = Booking.StatusChoices.CANCELLED
    booking.custom_data = custom_data


def cancel_booking(booking, user, action_source='user'):
    """
    Cancels a booking according to the SmartSlot refund policy rules.
    Returns a dict with success boolean and message to display to the user.
    """
    # If the booking is already cancelled, just return success
    if booking.status == Booking.StatusChoices.CANCELLED:
        return {
            'success': True,
            'message': 'This booking has already been cancelled.'
        }

    now = timezone.now()
    price = booking.resource.price
    payment = booking.payments.filter(status=Payment.StatusChoices.SUCCESS).first()

    # Rule 4: Booking has a resource price of 0 (Free booking)
    if price == 0:
        _cancel_booking_record(booking, 'free_booking_cancelled', 'cancelled')
        return {
            'success': True,
            'message': 'Your booking has been cancelled successfully. The slot is now available.'
        }

    if action_source == 'user':
        # Check timing: Rule 1 vs Rule 2
        time_difference = booking.start_time - now
        hours_before = time_difference.total_seconds() / 3600.0

        if hours_before > 24:
            # Rule 1: User cancels more than 24 hours before start time. Full refund.
            _cancel_booking_record(booking, 'user_cancelled_refund_due', 'refunded')
            
            if payment:
                payment.status = Payment.StatusChoices.REFUNDED
                payment.save(update_fields=['status'])
                
            return {
                'success': True,
                'message': 'Your booking has been cancelled, the slot is now available, and a full refund will be processed within 3-5 business days.'
            }
        else:
            # Rule 2: User cancels within 24 hours of start time. No refund.
            _cancel_booking_record(booking, 'user_cancelled_no_refund', 'no_refund')
            return {
                'success': True,
                'message': 'Your booking has been cancelled and the slot is now available. No refund is applicable for cancellations within 24 hours of the booking start time.'
            }

    elif action_source == 'admin':
        # Rule 3: Admin cancels the booking or marks resource as unavailable after payment confirmation.
        _cancel_booking_record(booking, 'admin_cancelled_refund_due', 'refunded')

        if payment:
            payment.status = Payment.StatusChoices.REFUNDED
            payment.save(update_fields=['status'])

        # Send apology email
        subject = 'SmartSlot - Booking Cancellation Apology'
        body = (
            f"Dear {booking.user.first_name or booking.user.username},\n\n"
            f"We sincerely apologize, but your booking for {booking.resource.name} on "
            f"{booking.start_time.strftime('%Y-%m-%d %H:%M')} has been cancelled because the resource "
            f"became unavailable.\n\n"
            f"A full refund of MWK {price:,.2f} has been processed back to your payment account.\n\n"
            f"Thank you for your understanding.\n"
            f"SmartSlot Support"
        )
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL or 'support@smartslot.com',
            recipient_list=[booking.user.email],
            fail_silently=True
        )

        return {
            'success': True,
            'message': 'This booking was cancelled by the organisation. The slot is now available and a full refund has been issued.'
        }

    elif action_source == 'no_show':
        # Rule 5: User fails to show up, admin marks as no show. No refund.
        booking.status = Booking.StatusChoices.NO_SHOW
        booking.save(update_fields=['status'])
        return {
            'success': True,
            'message': 'Booking marked as No Show. No refund is applicable.'
        }

    return {
        'success': False,
        'message': 'Invalid cancellation action.'
    }
