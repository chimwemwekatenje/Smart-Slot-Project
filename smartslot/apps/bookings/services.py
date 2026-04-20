"""
apps/bookings/services.py
-------------------------
All Firestore operations for the Bookings domain.

Every function is scoped to an organisation.  Views obtain the correct
organisation_id from  apps.core.services.get_org_id_for_user(request.user)
before calling these functions.

Firestore path
--------------
    organisations/{org_id}/bookings/{booking_id}

Document schema
---------------
    {
        "resource_id":     str,     # Firestore resource doc ID
        "resource_name":   str,     # denormalised for display without extra reads
        "user_id":         int,     # Django user pk
        "username":        str,     # denormalised
        "organisation_id": str,     # denormalised safety field
        "start_time":      str,     # ISO 8601 UTC string
        "end_time":        str,     # ISO 8601 UTC string
        "status":          str,     # Pending | Issued | Verified | Completed | Cancelled | NoShow
        "qr_token":        str,     # unique token for QR code verification
        "custom_data":     dict,    # extra fields (department, full_name, phone, etc.)
        "issued_at":       str | None,
        "verified_at":     str | None,
    }
"""

import uuid
import logging
from datetime import datetime, timezone

from apps.core.firebase import org_collection

logger = logging.getLogger(__name__)


# ── Status constants (mirrors Django model choices) ──────────────────────────

class BookingStatus:
    PENDING   = 'Pending'
    ISSUED    = 'Issued'
    VERIFIED  = 'Verified'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'
    NO_SHOW   = 'NoShow'
    ALL       = [PENDING, ISSUED, VERIFIED, COMPLETED, CANCELLED, NO_SHOW]


# ── Collection shortcut ──────────────────────────────────────────────────────

def _bookings_col(organisation_id: str):
    return org_collection(organisation_id, 'bookings')


# ── Read operations ──────────────────────────────────────────────────────────

def get_bookings_for_organisation(organisation_id: str, status: str = '') -> list[dict]:
    """
    Return all bookings for *organisation_id*, optionally filtered by status.

    Parameters
    ----------
    organisation_id : str
    status : str
        One of BookingStatus constants, or '' / 'All' to return everything.

    Returns
    -------
    list of dict  (sorted newest-first by start_time)
    """
    col = _bookings_col(organisation_id)

    if status and status != 'All':
        query = col.where('status', '==', status)
    else:
        query = col

    docs = query.stream()
    bookings = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        bookings.append(data)

    # Sort in Python (Firestore orderBy requires a composite index)
    bookings.sort(key=lambda b: b.get('start_time', ''), reverse=True)
    logger.debug(
        "Fetched %d bookings for org %s (status=%r)",
        len(bookings), organisation_id, status or 'All',
    )
    return bookings


def get_bookings_for_user(organisation_id: str, user_id: int, status: str = '') -> list[dict]:
    """
    Return bookings belonging to a specific user within an organisation.

    Employees and External users see only their own bookings; this function
    enforces that restriction at the Firestore query level.

    Parameters
    ----------
    organisation_id : str
    user_id : int
        Django User.pk
    status : str
        Optional status filter.
    """
    col = _bookings_col(organisation_id)
    query = col.where('user_id', '==', user_id)
    if status and status != 'All':
        query = query.where('status', '==', status)

    docs = query.stream()
    bookings = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        bookings.append(data)

    bookings.sort(key=lambda b: b.get('start_time', ''), reverse=True)
    return bookings


def get_all_bookings(status: str = '') -> list[dict]:
    """
    Return bookings across ALL organisations (PlatformAdmin only).

    The view layer must verify the user is a PlatformAdmin before calling
    this function.
    """
    from apps.core.firebase import get_firestore_client
    db = get_firestore_client()
    query = db.collection_group('bookings')
    if status and status != 'All':
        query = query.where('status', '==', status)

    docs = query.stream()
    bookings = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        bookings.append(data)

    bookings.sort(key=lambda b: b.get('start_time', ''), reverse=True)
    logger.debug("PlatformAdmin: fetched %d bookings across all orgs", len(bookings))
    return bookings


def get_booking_by_id(organisation_id: str, booking_id: str) -> dict | None:
    """
    Return a single booking document, or None if not found.

    Cross-tenant safety: verifies the document's organisation_id matches.
    """
    doc = _bookings_col(organisation_id).document(booking_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    if data.get('organisation_id') != str(organisation_id):
        logger.warning(
            "Booking %s claims org %s but was fetched under org %s — denied.",
            booking_id, data.get('organisation_id'), organisation_id,
        )
        return None
    data['id'] = doc.id
    return data


# ── Write operations ─────────────────────────────────────────────────────────

def create_booking(
    organisation_id: str,
    resource_id: str,
    resource_name: str,
    user,               # Django User instance
    start_time: datetime,
    end_time: datetime,
    custom_data: dict = None,
) -> str:
    """
    Create a new booking document in Firestore.

    Parameters
    ----------
    organisation_id : str
    resource_id : str
        Firestore document ID of the resource being booked.
    resource_name : str
        Denormalised resource name (avoids extra read on every list page).
    user : accounts.User
        The user making the booking.
    start_time, end_time : datetime (timezone-aware preferred)
    custom_data : dict | None
        Extra fields: department, full_name, phone, email, reason, etc.

    Returns
    -------
    str
        Firestore document ID of the new booking.
    """
    payload = {
        'resource_id':     str(resource_id),
        'resource_name':   resource_name,
        'user_id':         user.pk,
        'username':        user.username,
        'organisation_id': str(organisation_id),
        'start_time':      start_time.isoformat(),
        'end_time':        end_time.isoformat(),
        'status':          BookingStatus.PENDING,
        'qr_token':        str(uuid.uuid4()),
        'custom_data':     custom_data or {},
        'issued_at':       None,
        'verified_at':     None,
    }
    _, doc_ref = _bookings_col(organisation_id).add(payload)
    logger.info(
        "Created booking %s for resource %s in org %s by user %s",
        doc_ref.id, resource_id, organisation_id, user.username,
    )
    return doc_ref.id


def update_booking_status(
    organisation_id: str,
    booking_id: str,
    new_status: str,
) -> None:
    """
    Update only the status (and relevant timestamp) of a booking.

    Parameters
    ----------
    organisation_id : str
    booking_id : str
    new_status : str
        One of the BookingStatus constants.
    """
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    update_data = {'status': new_status}

    if new_status == BookingStatus.ISSUED:
        update_data['issued_at'] = now_iso
    elif new_status == BookingStatus.VERIFIED:
        update_data['verified_at'] = now_iso

    _bookings_col(organisation_id).document(booking_id).update(update_data)
    logger.info(
        "Booking %s in org %s updated to status %s",
        booking_id, organisation_id, new_status,
    )


def cancel_booking(organisation_id: str, booking_id: str) -> None:
    """Cancel a booking (shortcut for update_booking_status CANCELLED)."""
    update_booking_status(organisation_id, booking_id, BookingStatus.CANCELLED)
