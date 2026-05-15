from django.db import models
from apps.core.models import BaseModel
import uuid
import os
import mimetypes

# Roles that are scoped to a single organisation.
_ORG_SCOPED_ROLES = {'Employee', 'Receptionist', 'OrganisationAdmin'}

SUPABASE_BUCKET = 'media'


def _upload_to_supabase(file_field, folder: str) -> str:
    """Upload a Django file field to Supabase Storage and return the public URL."""
    from django.conf import settings
    from supabase import create_client

    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    ext = os.path.splitext(file_field.name)[1].lower()
    file_name = f"{folder}/{uuid.uuid4()}{ext}"
    content_type = mimetypes.guess_type(file_field.name)[0] or 'application/octet-stream'

    if hasattr(file_field, 'seek'):
        file_field.seek(0)
    data = file_field.read()

    sb.storage.from_(SUPABASE_BUCKET).upload(
        file_name, data, {'content-type': content_type, 'upsert': 'true'}
    )
    return sb.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)


class ResourceQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user or not user.is_authenticated:
            return self
        if user.is_superuser:
            return self
        if user.role == 'PlatformAdmin':
            return self
        if user.role == 'External':
            return self
        if user.role in _ORG_SCOPED_ROLES:
            if user.organisation_id:
                return self.filter(organisation_id=user.organisation_id)
            return self.none()
        return self.none()


class ResourceManager(models.Manager):
    def get_queryset(self):
        return ResourceQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)


class Resource(BaseModel):
    name          = models.CharField(max_length=255)
    description   = models.TextField(blank=True)
    photo         = models.ImageField(upload_to='resources_photos/', null=True, blank=True)
    # Stores the permanent Supabase Storage public URL after upload
    photo_url     = models.URLField(max_length=600, blank=True, null=True)
    price         = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    category      = models.CharField(max_length=255)
    custom_fields = models.JSONField(default=dict, blank=True)

    objects = ResourceManager()

    def save(self, *args, **kwargs):
        # If a new photo file has been attached, upload it to Supabase Storage
        if self.photo and hasattr(self.photo, 'file'):
            try:
                self.photo_url = _upload_to_supabase(self.photo.file, 'resources')
                # Clear the local file field so we don't store it on disk
                self.photo = None
            except Exception as e:
                # Log but don't crash — fall back to local storage
                import logging
                logging.getLogger(__name__).warning(f'Supabase upload failed: {e}')
        super().save(*args, **kwargs)

    @property
    def image(self):
        """Returns the best available image URL — Supabase first, local fallback."""
        if self.photo_url:
            return self.photo_url
        if self.photo:
            return self.photo.url
        return None

    def __str__(self):
        return self.name
