from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import BaseModel
from apps.resources.models import Resource


class Booking(BaseModel):
    class StatusChoices(models.TextChoices):
        PENDING   = 'Pending',   'Pending'
        BOOKED    = 'Booked',    'Booked'
        CANCELLED = 'Cancelled', 'Cancelled'

    # Active statuses — used for overlap detection
    ACTIVE_STATUSES = ['Pending', 'Booked']

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    start_time = models.DateTimeField()
    end_time   = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.BOOKED,
    )
    issued_at   = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    qr_token    = models.CharField(max_length=255, unique=True)
    custom_data = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['resource', 'start_time', 'end_time']),
        ]

    def __str__(self):
        return f"Booking #{self.id} — {self.resource.name} by {self.user.username}"

    def clean(self):
        """Raise ValidationError if this booking overlaps an existing active one."""
        if not self.start_time or not self.end_time:
            return
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

        overlapping = (
            Booking.objects
            .filter(
                resource=self.resource,
                status__in=self.ACTIVE_STATUSES,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
            .exclude(pk=self.pk)
        )
        if overlapping.exists():
            conflict = overlapping.first()
            raise ValidationError(
                f"This resource is already booked from "
                f"{conflict.start_time.strftime('%d %b %Y %H:%M')} to "
                f"{conflict.end_time.strftime('%H:%M')}. "
                f"Please choose a different time slot."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES

    @classmethod
    def is_resource_booked_now(cls, resource):
        now = timezone.now()
        return cls.objects.filter(
            resource=resource,
            status__in=cls.ACTIVE_STATUSES,
            start_time__lte=now,
            end_time__gt=now,
        ).exists()
