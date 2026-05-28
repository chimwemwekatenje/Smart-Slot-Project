from django.utils import timezone
from apps.bookings.models import Booking
from .models import VerificationLog


class VerificationService:
    """Service for handling booking verification logic"""
    
    @staticmethod
    def verify_booking(qr_token: str, verified_by_user) -> dict:
        """
        Verify a booking using its QR token.
        Returns a dict with success status and message.
        """
        try:
            booking = Booking.objects.select_related(
                'resource', 'user', 'organisation'
            ).get(qr_token=qr_token)
        except Booking.DoesNotExist:
            # Log failed attempt
            VerificationLog.objects.create(
                verified_by=verified_by_user,
                action='Verify',
                qr_token=qr_token,
                success=False,
                notes='Booking not found',
            )
            return {
                'success': False,
                'message': 'Invalid QR code. Booking not found.',
            }
        
        # Check if booking is in a verifiable state
        if booking.status not in ['Issued', 'Pending']:
            VerificationLog.objects.create(
                booking=booking,
                verified_by=verified_by_user,
                action='Verify',
                qr_token=qr_token,
                success=False,
                notes=f'Booking status is {booking.status}',
            )
            return {
                'success': False,
                'message': f'Booking cannot be verified. Current status: {booking.status}',
                'booking': booking,
            }
        
        # Check if user has permission to verify this booking
        if verified_by_user.role not in ['PlatformAdmin', 'OrganisationAdmin', 'Receptionist']:
            VerificationLog.objects.create(
                booking=booking,
                verified_by=verified_by_user,
                action='Verify',
                qr_token=qr_token,
                success=False,
                notes='User does not have permission to verify',
            )
            return {
                'success': False,
                'message': 'You do not have permission to verify bookings.',
            }
        
        # Check if receptionist is verifying their own org's booking
        if verified_by_user.role in ['OrganisationAdmin', 'Receptionist']:
            if verified_by_user.organisation != booking.organisation:
                VerificationLog.objects.create(
                    booking=booking,
                    verified_by=verified_by_user,
                    action='Verify',
                    qr_token=qr_token,
                    success=False,
                    notes='User cannot verify bookings from other organisations',
                )
                return {
                    'success': False,
                    'message': 'You can only verify bookings from your organisation.',
                }
        
        # All checks passed - verify the booking
        booking.status = 'Verified'
        booking.verified_at = timezone.now()
        booking.save()
        
        # Log successful verification
        VerificationLog.objects.create(
            booking=booking,
            verified_by=verified_by_user,
            action='Verify',
            qr_token=qr_token,
            success=True,
            notes='Booking verified successfully',
        )
        
        return {
            'success': True,
            'message': 'Booking verified successfully!',
            'booking': booking,
        }
    
    @staticmethod
    def complete_booking(qr_token: str, completed_by_user, notes: str = '') -> dict:
        """
        Mark a verified booking as completed.
        """
        try:
            booking = Booking.objects.select_related(
                'resource', 'user', 'organisation'
            ).get(qr_token=qr_token)
        except Booking.DoesNotExist:
            VerificationLog.objects.create(
                verified_by=completed_by_user,
                action='Complete',
                qr_token=qr_token,
                success=False,
                notes='Booking not found',
            )
            return {
                'success': False,
                'message': 'Invalid QR code. Booking not found.',
            }
        
        # Check if booking is verified
        if booking.status != 'Verified':
            VerificationLog.objects.create(
                booking=booking,
                verified_by=completed_by_user,
                action='Complete',
                qr_token=qr_token,
                success=False,
                notes=f'Booking status is {booking.status}, must be Verified',
            )
            return {
                'success': False,
                'message': f'Booking must be verified first. Current status: {booking.status}',
                'booking': booking,
            }
        
        # Check permissions
        if completed_by_user.role not in ['PlatformAdmin', 'OrganisationAdmin', 'Receptionist']:
            VerificationLog.objects.create(
                booking=booking,
                verified_by=completed_by_user,
                action='Complete',
                qr_token=qr_token,
                success=False,
                notes='User does not have permission',
            )
            return {
                'success': False,
                'message': 'You do not have permission to complete bookings.',
            }
        
        # Check organisation match
        if completed_by_user.role in ['OrganisationAdmin', 'Receptionist']:
            if completed_by_user.organisation != booking.organisation:
                VerificationLog.objects.create(
                    booking=booking,
                    verified_by=completed_by_user,
                    action='Complete',
                    qr_token=qr_token,
                    success=False,
                    notes='User cannot complete bookings from other organisations',
                )
                return {
                    'success': False,
                    'message': 'You can only complete bookings from your organisation.',
                }
        
        # Mark as completed
        booking.status = 'Completed'
        booking.save()
        
        # Log completion
        VerificationLog.objects.create(
            booking=booking,
            verified_by=completed_by_user,
            action='Complete',
            qr_token=qr_token,
            success=True,
            notes=notes or 'Booking completed',
        )
        
        return {
            'success': True,
            'message': 'Booking marked as completed!',
            'booking': booking,
        }
