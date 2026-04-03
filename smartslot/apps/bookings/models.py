from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.resources.models import Resource

class Booking(BaseModel):
    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        ISSUED = 'Issued', 'Issued'
        VERIFIED = 'Verified', 'Verified'
        COMPLETED = 'Completed', 'Completed'
        CANCELLED = 'Cancelled', 'Cancelled'
        NO_SHOW = 'NoShow', 'No Show'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    resource = models.ForeignKey(
        Resource, 
        on_delete=models.CASCADE, 
        related_name='bookings'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    qr_token = models.CharField(max_length=255, unique=True)
    custom_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Booking {self.id} for {self.resource.name} by {self.user.username}"
