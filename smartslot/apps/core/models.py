import uuid
import base64
from django.db import models

class Organisation(models.Model):
    name        = models.CharField(max_length=255)
    logo        = models.ImageField(upload_to='organisation_logos/', null=True, blank=True)
    # Set to True when the Super Admin approves the organisation application.
    # Only approved organisations (and their resources) are visible to users.
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields', None)
        is_approved_changed = None  # True if approved, False if revoked, None if no change
        if self.pk:
            try:
                old_org = Organisation.objects.get(pk=self.pk)
                if self.is_approved and not old_org.is_approved:
                    is_approved_changed = True
                elif not self.is_approved and old_org.is_approved:
                    is_approved_changed = False
            except Organisation.DoesNotExist:
                pass
        else:
            if self.is_approved:
                is_approved_changed = True

        if is_approved_changed is True:
            if not self.approved_at:
                from django.utils import timezone
                self.approved_at = timezone.now()
                if update_fields is not None:
                    update_fields = set(update_fields)
                    update_fields.add('approved_at')
                    kwargs['update_fields'] = list(update_fields)
        elif is_approved_changed is False:
            self.approved_at = None
            if update_fields is not None:
                update_fields = set(update_fields)
                update_fields.add('approved_at')
                kwargs['update_fields'] = list(update_fields)

        super().save(*args, **kwargs)

        if is_approved_changed is True:
            from apps.resources.models import Resource
            Resource.objects.filter(organisation=self).update(is_active=True)
        elif is_approved_changed is False:
            from apps.resources.models import Resource
            Resource.objects.filter(organisation=self).update(is_active=False)


class OrganisationApplication(models.Model):
    class StatusChoices(models.TextChoices):
        SUBMITTED = 'Submitted', 'Submitted'
        UNDER_REVIEW = 'UnderReview', 'Under Review'
        REJECTED = 'Rejected', 'Rejected'
        APPROVED_FOR_PAYMENT = 'ApprovedForPayment', 'Approved for Payment'
        PAID = 'Paid', 'Paid'
        COMPLETED = 'Completed', 'Completed'

    organisation_name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='organisation_applications/logos/', null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=StatusChoices.choices,
        default=StatusChoices.SUBMITTED,
    )
    rejection_reason = models.TextField(blank=True)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_organisation = models.ForeignKey(
        Organisation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.organisation_name} ({self.get_status_display()})"

    @property
    def all_resources_verified(self):
        resources = self.resources.all()
        return resources.exists() and all(resource.is_verified for resource in resources)


class ApplicationResource(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        VERIFIED = 'Verified', 'Verified'
        REJECTED = 'Rejected', 'Rejected'

    application = models.ForeignKey(
        OrganisationApplication,
        on_delete=models.CASCADE,
        related_name='resources',
    )
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    image_data = models.TextField(blank=True)
    image_mime = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    admin_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.application.organisation_name}"

    @property
    def is_verified(self):
        return self.status == self.StatusChoices.VERIFIED

    @property
    def image_src(self):
        if not self.image_data or not self.image_mime:
            return ''
        return f"data:{self.image_mime};base64,{self.image_data}"

    def set_image_file(self, image_file):
        if not image_file:
            self.image_data = ''
            self.image_mime = ''
            return
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        self.image_data = base64.b64encode(image_file.read()).decode('ascii')
        self.image_mime = getattr(image_file, 'content_type', '') or 'image/jpeg'


class BaseModel(models.Model):
    organisation = models.ForeignKey(
        Organisation, 
        on_delete=models.CASCADE, 
        related_name="%(app_label)s_%(class)s_related"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
