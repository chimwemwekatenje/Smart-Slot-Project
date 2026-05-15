import uuid
from django.db import models

class Organisation(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='organisation_logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self):
        return self.name


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
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.application.organisation_name}"

    @property
    def is_verified(self):
        return self.status == self.StatusChoices.VERIFIED


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
