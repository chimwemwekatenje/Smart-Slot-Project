from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        PLATFORM_ADMIN = 'PlatformAdmin', 'Platform Admin'
        ORGANISATION_ADMIN = 'OrganisationAdmin', 'Organisation Admin'
        RECEPTIONIST = 'Receptionist', 'Receptionist'
        EMPLOYEE = 'Employee', 'Employee'
        EXTERNAL = 'External', 'External'

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.EXTERNAL,
    )

    # Link to an organisation (null for external users)
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )

    phone = models.CharField(max_length=20, blank=True)

    # Resolve related_name clashes with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name="custom_user_set",
        related_query_name="user",
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
