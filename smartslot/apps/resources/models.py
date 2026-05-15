import os
import uuid
import mimetypes
from django.db import models
from django.conf import settings
from apps.core.models import BaseModel


# Roles that are scoped to a single organisation.
# Any role NOT in this set sees all resources.
_ORG_SCOPED_ROLES = {'Employee', 'Receptionist', 'OrganisationAdmin'}


class ResourceQuerySet(models.QuerySet):
    def visible_to(self, user):
        """
        Return the subset of resources the given user is allowed to see.

        Rules
        -----
        - Anonymous / unauthenticated  → all resources (public browsing)
        - External role                → all resources (cross-org booking)
        - PlatformAdmin / superuser    → all resources (platform-wide view)
        - Employee / Receptionist /
          OrganisationAdmin            → only their own organisation's resources
        """
        if not user or not user.is_authenticated:
            return self                          # guest — show everything

        if user.is_superuser:
            return self                          # Django superuser — show everything

        if user.role == 'PlatformAdmin':
            return self                          # platform-wide admin — show everything

        if user.role == 'External':
            return self                          # external booker — show everything

        # Internal roles: scope to the user's own organisation
        if user.role in _ORG_SCOPED_ROLES:
            if user.organisation_id:
                return self.filter(organisation_id=user.organisation_id)
            # Internal user with no org assigned — show nothing (safe default)
            return self.none()

        # Unknown / future role — safe default: show nothing
        return self.none()


class ResourceManager(models.Manager):
    def get_queryset(self):
        return ResourceQuerySet(self.model, using=self._db)

    def visible_to(self, user):
        """Shortcut: Resource.objects.visible_to(user)"""
        return self.get_queryset().visible_to(user)


class Resource(BaseModel):
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='resources_photos/', null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category = models.CharField(max_length=255)
    photo       = models.ImageField(upload_to='resources_photos/', null=True, blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category    = models.CharField(max_length=255)
    custom_fields = models.JSONField(default=dict, blank=True)

    objects = ResourceManager()

    def save(self, *args, **kwargs):
        upload_photo = False
        if self.photo:
            if not self.pk:
                upload_photo = True
            else:
                orig = Resource.objects.get(pk=self.pk)
                if orig.photo != self.photo:
                    upload_photo = True

        if upload_photo and self.photo:
            try:
                from supabase import create_client, Client
                
                # Create Supabase client
                supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                
                # Generate unique filename
                ext = os.path.splitext(self.photo.name)[1]
                file_name = f"resources/{uuid.uuid4()}{ext}"
                
                # Ensure we are at the start of the file
                if hasattr(self.photo.file, 'seek'):
                    self.photo.file.seek(0)
                file_data = self.photo.file.read()
                
                content_type = mimetypes.guess_type(self.photo.name)[0] or 'application/octet-stream'
                
                # Upload to Supabase storage 'media' bucket
                supabase.storage.from_("media").upload(
                    file_name, 
                    file_data, 
                    {"content-type": content_type}
                )
                
                # Get and set public URL
                public_url = supabase.storage.from_("media").get_public_url(file_name)
                self.image_url = public_url
            except Exception as e:
                print(f"Error uploading to Supabase: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
