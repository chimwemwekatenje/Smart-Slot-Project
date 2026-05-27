from django.db import models
from django.conf import settings
from apps.bookings.models import Booking


class VerificationLog(models.Model):
    """Log of all verification attempts (successful or failed)"""
    
    class ActionChoices(models.TextChoices):
        VERIFY = 'Verify', 'Verify'
        COMPLETE = 'Complete', 'Complete'
        REJECT = 'Reject', 'Reject'
    
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='verification_logs',
        null=True,
        blank=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications_performed',
    )
    action = models.CharField(
        max_length=20,
        choices=ActionChoices.choices,
    )
    qr_token = models.CharField(max_length=255)
    success = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.action} - {status} - {self.qr_token[:8]}... at {self.timestamp}"
