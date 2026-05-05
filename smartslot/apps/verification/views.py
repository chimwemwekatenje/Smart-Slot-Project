from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import VerificationService
from apps.api.serializers import BookingSerializer


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
