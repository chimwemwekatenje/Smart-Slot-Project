"""
apps/bookings/api_views.py
--------------------------
REST API endpoints for bookings — consumed by the Flutter mobile app.

Endpoints
---------
GET  /api/bookings/          → list bookings (role-scoped)
POST /api/bookings/          → create a new booking
GET  /api/bookings/<id>/     → detail for a single booking
POST /api/bookings/<id>/cancel/ → cancel a booking
"""

from datetime import datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from apps.core.services import get_org_id_for_user, assert_same_org
from apps.bookings.services import (
    BookingStatus,
    get_bookings_for_organisation,
    get_bookings_for_user,
    get_all_bookings,
    get_booking_by_id,
    create_booking,
    cancel_booking,
)
from apps.resources.services import get_resource_by_id, get_all_resources

_ORG_WIDE_ROLES = {'PlatformAdmin', 'OrganisationAdmin', 'Receptionist'}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_booking_list(request):
    """
    GET:  List bookings scoped by role.
    POST: Create a new booking.
          Body: { resource_id, start_time (ISO), end_time (ISO), custom_data (dict) }
    """
    user = request.user

    try:
        org_id = get_org_id_for_user(user)
    except PermissionDenied as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        status_filter = request.query_params.get('status', '')

        if user.is_platform_admin:
            bookings = get_all_bookings(status=status_filter)
        elif user.role in _ORG_WIDE_ROLES:
            bookings = get_bookings_for_organisation(org_id, status=status_filter)
        else:
            bookings = get_bookings_for_user(org_id, user_id=user.pk, status=status_filter)
        return Response(bookings)

    # POST — create booking
    data = request.data
    required = ['resource_id', 'start_time', 'end_time']
    errors = {f: ['This field is required.'] for f in required if not data.get(f)}
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    resource_id = int(data['resource_id'])

    # Resolve resource (and verify org access)
    if user.is_platform_admin:
        all_res = get_all_resources()
        matches = [r for r in all_res if r['id'] == resource_id]
        if not matches:
            return Response({'detail': 'Resource not found.'}, status=status.HTTP_404_NOT_FOUND)
        resource = matches[0]
        booking_org_id = resource['organisation_id']
    else:
        resource = get_resource_by_id(org_id, resource_id)
        if resource is None:
            return Response({'detail': 'Resource not found in your organisation.'}, status=status.HTTP_404_NOT_FOUND)
        booking_org_id = org_id

    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time   = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return Response({'detail': 'start_time and end_time must be valid ISO 8601 datetime strings.'},
                        status=status.HTTP_400_BAD_REQUEST)

    booking_id = create_booking(
        organisation_id=booking_org_id,
        resource_id=resource_id,
        resource_name=resource['name'],
        user=user,
        start_time=start_time,
        end_time=end_time,
        custom_data=data.get('custom_data', {}),
    )
    booking = get_booking_by_id(booking_org_id, booking_id)
    return Response(booking, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_booking_detail(request, pk: int):
    """Return a single booking (user must own it or have org-wide access)."""
    user = request.user
    try:
        org_id = get_org_id_for_user(user)
    except PermissionDenied as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

    if user.is_platform_admin:
        bookings = get_all_bookings()
        matches = [b for b in bookings if b['id'] == pk]
        booking = matches[0] if matches else None
    else:
        booking = get_booking_by_id(org_id, pk)

    if booking is None:
        return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Non-admin users can only see their own bookings
    if user.role not in _ORG_WIDE_ROLES and booking['user_id'] != user.pk:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    return Response(booking)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_booking_cancel(request, pk: int):
    """Cancel a booking. Users can only cancel their own; admins can cancel any."""
    user = request.user
    try:
        org_id = get_org_id_for_user(user)
    except PermissionDenied as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_403_FORBIDDEN)

    booking_org_id = org_id if org_id else None

    # For PlatformAdmin we need to find the org
    if user.is_platform_admin:
        all_b = get_all_bookings()
        matches = [b for b in all_b if b['id'] == pk]
        if not matches:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        booking_org_id = matches[0]['organisation_id']
        booking = matches[0]
    else:
        booking = get_booking_by_id(org_id, pk)
        if booking is None:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Non-admin users can only cancel their own bookings
    if user.role not in _ORG_WIDE_ROLES and booking['user_id'] != user.pk:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    cancel_booking(booking_org_id, pk)
    return Response({'detail': 'Booking cancelled.'})
