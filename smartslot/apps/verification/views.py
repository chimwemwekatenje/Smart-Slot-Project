from django.shortcuts import render, get_object_or_404
from apps.bookings.models import Booking


STATUS_COLORS = {
    'Pending':   '#F59E0B',
    'Issued':    '#14B8A6',
    'Verified':  '#22C55E',
    'Completed': '#22C55E',
    'Cancelled': '#EF4444',
    'NoShow':    '#EF4444',
}


def verify_booking_view(request, qr_token):
    """
    Public view — no authentication required.
    Resolves a QR token to a full booking verification page.
    """
    booking = get_object_or_404(Booking, qr_token=qr_token)

    status_color = STATUS_COLORS.get(booking.status, '#94A3B8')

    customer_name = (
        booking.custom_data.get('full_name')
        or booking.user.get_full_name()
        or booking.user.username
    )

    fmt = lambda dt: dt.strftime('%a %d %b %Y, %H:%M') if dt else '-'

    rows = [
        ('Customer',     customer_name),
        ('Resource',     booking.resource.name),
        ('Organisation', booking.organisation.name),
        ('Category',     booking.resource.category),
        ('From',         fmt(booking.start_time.astimezone())),
        ('To',           fmt(booking.end_time.astimezone())),
        ('Booking ID',   f'#{booking.id}'),
    ]

    return render(request, 'verification/verify.html', {
        'booking':       booking,
        'status_color':  status_color,
        'customer_name': customer_name,
        'rows':          rows,
    })
