from django.db import models
from apps.core.models import BaseModel

class Resource(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='resources_photos/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category = models.CharField(max_length=255)
    custom_fields = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name
