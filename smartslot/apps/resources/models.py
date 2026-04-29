from django.db import models
from apps.core.models import BaseModel

class Resource(BaseModel):
    RESOURCE_TYPES = [
        ('boardroom', 'Boardroom'),
        ('vehicle', 'Vehicle'),
        ('projector', 'Projector'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES)
    capacity = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_available = models.BooleanField(default=True)
    image_url = models.URLField(max_length=1024, blank=True, null=True)

    class Meta:
        db_table = 'resources'
        verbose_name = "Resource"
        verbose_name_plural = "Resources"

    def __str__(self):
        return self.name
