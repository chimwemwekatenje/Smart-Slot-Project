from django.db import models
from apps.core.models import BaseModel
import uuid
import os
import mimetypes
import base64

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
            organisation_id = getattr(user, 'organisation_id', None)
            if not organisation_id and user.role == 'OrganisationAdmin':
                try:
                    from apps.core.mixins import get_user_organisation
                    organisation = get_user_organisation(user)
                    organisation_id = getattr(organisation, 'id', None)
                except Exception:
                    organisation_id = None
            if organisation_id:
                # Org-scoped staff see their own resources even before the
                # organisation is fully activated, so admins can manage them.
                return self.filter(organisation_id=organisation_id)
            return self.none()
        return self.none()


class ResourceManager(models.Manager):
    def get_queryset(self):
        return ResourceQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        return self.get_queryset().visible_to(user)


class Resource(BaseModel):
    class CategoryChoices(models.TextChoices):
        BOARDROOM      = 'Boardroom',       'Boardroom'
        EQUIPMENT      = 'Equipment',       'Equipment'
        VEHICLE        = 'Vehicle',         'Vehicle'
        WORKSPACE      = 'Workspace',       'Workspace'
        IT_TECHNOLOGY  = 'IT & Technology', 'IT & Technology'
        FACILITY       = 'Facility',        'Facility'
        CATERING       = 'Catering',        'Catering'
        OTHER          = 'Other',           'Other'

    name          = models.CharField(max_length=255)
    description   = models.TextField(blank=True)
    photo         = models.ImageField(upload_to='resources_photos/', null=True, blank=True)
    # Stores the permanent Supabase Storage public URL after upload
    image_url     = models.URLField(max_length=600, blank=True, null=True)
    photo_url     = models.URLField(max_length=600, blank=True, null=True)
    photo_data    = models.TextField(blank=True)
    photo_mime    = models.CharField(max_length=100, blank=True)
    price         = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    category      = models.CharField(
        max_length=255,
        choices=CategoryChoices.choices,
    )
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

        # Store uploaded images in the database so they survive Render deploys
        # without depending on local disk or external storage configuration.
        if self.photo and hasattr(self.photo, 'file'):
            try:
                file_obj = self.photo.file
                if hasattr(file_obj, 'seek'):
                    file_obj.seek(0)
                self.photo_data = base64.b64encode(file_obj.read()).decode('ascii')
                self.photo_mime = (
                    getattr(file_obj, 'content_type', '')
                    or mimetypes.guess_type(self.photo.name)[0]
                    or 'image/jpeg'
                )
                self.photo = None
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Database image storage failed: {e}')
        super().save(*args, **kwargs)

    @property
    def image(self):
        """Returns the best available image URL — Supabase first, local fallback, placeholder default."""
        from django.conf import settings
        if self.photo_data and self.photo_mime:
            return f"data:{self.photo_mime};base64,{self.photo_data}"
        if self.image_url:
            return self.image_url
        if self.photo_url:
            return self.photo_url
        if self.photo:
            return self.photo.url
        return f"{settings.STATIC_URL}img/placeholder.png"

    def __str__(self):
        return self.name
