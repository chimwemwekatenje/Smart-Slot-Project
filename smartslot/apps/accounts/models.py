from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        PLATFORM_ADMIN = 'PlatformAdmin', 'Platform Admin'
        ORGANISATION_ADMIN = 'OrganisationAdmin', 'Organisation Admin'
        RECEPTIONIST = 'Receptionist', 'Receptionist'
        EMPLOYEE = 'Employee', 'Employee'

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.EMPLOYEE,
    )

    # Resolve related_name clashes with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="user",
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
