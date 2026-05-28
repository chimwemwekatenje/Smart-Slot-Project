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
    def active(self):
        """Only resources that are active AND belong to an approved organisation."""
        return self.filter(is_active=True, organisation__is_approved=True)

    def visible_to(self, user):
        """
        Scope resources by role, then restrict to active/approved only.
        Superusers and PlatformAdmins see everything (including inactive/unapproved)
        so they can manage the full catalogue.
        """
        if not user or not user.is_authenticated:
            # Unauthenticated visitors only see active resources from approved orgs
            return self.active()
        if user.is_superuser or user.role == 'PlatformAdmin':
            return self  # full visibility for admins
        if user.role == 'External':
            return self.active()
        if user.role in _ORG_SCOPED_ROLES:
            if user.organisation_id:
                # Org-scoped staff see their own org's resources (active or not)
                # so they can manage them, but only if the org is approved
                return self.filter(
                    organisation_id=user.organisation_id,
                    organisation__is_approved=True,
                )
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
    image_url     = models.URLField(max_length=600, blank=True, null=True)
    photo_url     = models.URLField(max_length=600, blank=True, null=True)
    price         = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    category      = models.CharField(max_length=255)
    custom_fields = models.JSONField(default=dict, blank=True)
    # Activated automatically when the parent organisation is approved.
    # Org admins can also deactivate individual resources manually.
    is_active     = models.BooleanField(default=False)

    objects = ResourceManager()

    def save(self, *args, **kwargs):
        # Auto-activate resource if its organisation is already approved and it's new
        if not self.pk:
            if self.organisation and self.organisation.is_approved:
                self.is_active = True

        # If a new photo file has been attached, upload it to Supabase Storage
        if self.photo and hasattr(self.photo, 'file'):
            try:
                public_url = _upload_to_supabase(self.photo.file, 'resources')
                self.image_url = public_url
                self.photo_url = public_url
                # Clear the local file field so we don't store it on disk
                self.photo = None
            except Exception as e:
                # Log but don't crash — fall back to local storage
                import logging
                logging.getLogger(__name__).warning(f'Supabase upload failed: {e}')
        super().save(*args, **kwargs)

    @property
    def image(self):
        """Returns the best available image URL — Supabase first, local fallback, placeholder default."""
        from django.conf import settings
        if self.image_url:
            return self.image_url
        if self.photo_url:
            return self.photo_url
        if self.photo:
            return self.photo.url
        return f"{settings.STATIC_URL}img/placeholder.png"

    def __str__(self):
        return self.name
