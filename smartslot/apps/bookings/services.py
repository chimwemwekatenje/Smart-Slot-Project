"""
apps/bookings/services.py
-------------------------
All database operations for the Bookings domain.
"""

import uuid
import logging
import base64
import io
import qrcode
from datetime import datetime
from django.utils import timezone as dj_timezone

from apps.bookings.models import Booking
from apps.resources.models import Resource

logger = logging.getLogger(__name__)



class BookingStatus:
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    NO_SHOW = 'no_show'
    ALL = [PENDING, CONFIRMED, CANCELLED, COMPLETED, NO_SHOW]


# â”€â”€ Internal helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _generate_qr_base64(data: str) -> str:
    """Generate a base64 encoded QR code PNG string from data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

def _booking_to_dict(b: Booking) -> dict:
    """Convert a Booking ORM instance to a dict."""
    return {
        'id':              str(b.pk),
        'resource_id':     str(b.resource_id),
        'resource_name':   b.resource.name if hasattr(b, 'resource') and b.resource else '',
        'user_id':         str(b.user_id),
        'username':        b.user.username if hasattr(b, 'user') and b.user else '',
        'organisation_id': str(b.organisation_id),
        'title':           b.title,
        'purpose':         b.purpose,
        'start_time':      b.start_time.isoformat() if b.start_time else None,
        'end_time':        b.end_time.isoformat() if b.end_time else None,
        'status':          b.status,
        'qr_code':         b.qr_code,
        'total_price':     str(b.total_price),
        'notes':           b.notes,
        'created_at':      b.created_at.isoformat() if b.created_at else None,
    }


def _qs_to_dicts(qs) -> list[dict]:
    """Convert a Booking queryset to a list of dicts, newest-first."""
    bookings = qs.select_related('resource', 'user').order_by('-start_time')
    return [_booking_to_dict(b) for b in bookings]


# â”€â”€ Read operations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_bookings_for_organisation(organisation_id, status: str = '') -> list[dict]:
    qs = Booking.objects.filter(organisation_id=organisation_id)
    if status and status != 'All':
        qs = qs.filter(status=status)
    return _qs_to_dicts(qs)


def get_bookings_for_user(organisation_id, user_id, status: str = '') -> list[dict]:
    qs = Booking.objects.filter(organisation_id=organisation_id, user_id=user_id)
    if status and status != 'All':
        qs = qs.filter(status=status)
    return _qs_to_dicts(qs)


def get_all_bookings(status: str = '') -> list[dict]:
    qs = Booking.objects.all()
    if status and status != 'All':
        qs = qs.filter(status=status)
    return _qs_to_dicts(qs)


def get_booking_by_id(organisation_id, booking_id) -> dict | None:
    try:
        b = Booking.objects.select_related('resource', 'user').get(
            pk=booking_id,
            organisation_id=organisation_id,
        )
    except Booking.DoesNotExist:
        return None
    return _booking_to_dict(b)


# â”€â”€ Write operations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_booking(
    organisation_id,
    resource_id,
    user,               # Django User instance
    start_time: datetime,
    end_time: datetime,
    title: str,
    purpose: str,
    total_price: float = 0.00,
    notes: str = '',
):
    """
    Create a new Booking row and generate a QR code for it.
    """
    booking = Booking.objects.create(
        organisation_id=organisation_id,
        resource_id=resource_id,
        user=user,
        start_time=start_time,
        end_time=end_time,
        title=title,
        purpose=purpose,
        status='pending',
        total_price=total_price,
        notes=notes,
    )
    
    # Generate QR Code with booking UUID
    qr_data = f"smartslot_booking:{booking.pk}"
    booking.qr_code = _generate_qr_base64(qr_data)
    booking.save(update_fields=['qr_code'])
    
    logger.info(
        "Created booking %s for resource %s in org %s by user %s",
        booking.pk, resource_id, organisation_id, user.username,
    )
    return booking.pk


def update_booking_status(
    organisation_id,
    booking_id,
    new_status: str,
) -> None:
    Booking.objects.filter(pk=booking_id, organisation_id=organisation_id).update(status=new_status)
    logger.info("Booking %s in org %s updated to status %s", booking_id, organisation_id, new_status)


def cancel_booking(organisation_id, booking_id) -> None:
    update_booking_status(organisation_id, booking_id, 'cancelled')
