from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from apps.bookings.models import Booking
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import qrcode
import qrcode.image.svg
import io
import base64
from .services import VerificationService
from apps.api.serializers import BookingSerializer

STATUS_COLORS = {
    'Pending':   '#F59E0B',
    'Booked':    '#14B8A6',
    'Cancelled': '#EF4444',
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


class PublicReceiptView(APIView):
    """
    Public web page showing a booking receipt when someone scans the QR code.
    GET /receipt/<qr_token>/
    No authentication required — the token itself is the secret.
    """
    permission_classes = [AllowAny]

    def get(self, request, qr_token):
        from apps.bookings.models import Booking

        try:
            booking = Booking.objects.select_related(
                'resource', 'user', 'organisation'
            ).get(qr_token=qr_token)
        except Booking.DoesNotExist:
            return render(request, 'receipt.html', {'booking': None})

        # Build QR code as base64 PNG to embed in the page
        receipt_url = request.build_absolute_uri(f'/receipt/{qr_token}/')
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(receipt_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_b64 = base64.b64encode(buffer.getvalue()).decode()
        qr_image_url = f'data:image/png;base64,{qr_b64}'

        # Extract custom data
        custom = booking.custom_data or {}
        user = booking.user
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username

        context = {
            'booking': booking,
            'booked_by': full_name,
            'department': custom.get('department', ''),
            'reason': custom.get('reason', ''),
            'qr_image_url': qr_image_url,
            'generated_at': timezone.now().strftime('%d %b %Y, %H:%M'),
        }
        return render(request, 'receipt.html', context)


class VerifyBookingView(APIView):
    """
    POST endpoint for receptionists to verify a booking by scanning QR code.
    Expects: {"qr_token": "uuid-string"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        qr_token = request.data.get('qr_token', '').strip()
        
        if not qr_token:
            return Response(
                {'detail': 'QR token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        result = VerificationService.verify_booking(qr_token, request.user)
        
        if result['success']:
            return Response({
                'detail': result['message'],
                'booking': BookingSerializer(result['booking']).data,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': result['message']},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CompleteBookingView(APIView):
    """
    POST endpoint to mark a verified booking as completed.
    Expects: {"qr_token": "uuid-string", "notes": "optional notes"}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        qr_token = request.data.get('qr_token', '').strip()
        notes = request.data.get('notes', '')
        
        if not qr_token:
            return Response(
                {'detail': 'QR token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        result = VerificationService.complete_booking(qr_token, request.user, notes)
        
        if result['success']:
            return Response({
                'detail': result['message'],
                'booking': BookingSerializer(result['booking']).data,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': result['message']},
                status=status.HTTP_400_BAD_REQUEST,
            )


class BookingDetailByTokenView(APIView):
    """
    GET endpoint to retrieve booking details by QR token (for preview before verification).
    GET /api/verification/booking/?qr_token=uuid-string
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from apps.bookings.models import Booking
        
        qr_token = request.query_params.get('qr_token', '').strip()
        
        if not qr_token:
            return Response(
                {'detail': 'QR token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            booking = Booking.objects.select_related(
                'resource', 'user', 'organisation'
            ).get(qr_token=qr_token)
        except Booking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check if user has permission to view this booking
        user = request.user
        if user.role in ['OrganisationAdmin', 'Receptionist']:
            if user.organisation != booking.organisation:
                return Response(
                    {'detail': 'You do not have permission to view this booking.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif user.role == 'Employee' or user.role == 'External':
            if booking.user != user:
                return Response(
                    {'detail': 'You do not have permission to view this booking.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        
        return Response(BookingSerializer(booking).data)

