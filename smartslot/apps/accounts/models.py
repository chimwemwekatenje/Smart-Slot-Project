"""
apps/accounts/models.py
-----------------------
Custom User model with role-based access control and organisation scoping.

Roles
-----
- PlatformAdmin    : super-admin, sees ALL organisations and their data
- OrganisationAdmin: manages one organisation (resources, users, bookings)
- Receptionist     : processes bookings for their organisation
- Employee         : makes personal bookings within their organisation
- External         : external/guest users; paid bookings only
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        PLATFORM_ADMIN      = 'PlatformAdmin',      'Platform Admin'
        ORGANISATION_ADMIN  = 'OrganisationAdmin',  'Organisation Admin'
        RECEPTIONIST        = 'Receptionist',        'Receptionist'
        EMPLOYEE            = 'Employee',            'Employee'
        EXTERNAL            = 'External',            'External'

    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.EMPLOYEE,
    )

    # The organisation this user belongs to.
    # PlatformAdmin users leave this NULL — they span all organisations.
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        help_text=(
            "The organisation this user belongs to. "
            "Leave blank for Platform Admins."
        ),
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

    # ── Computed helpers ──────────────────────────────────────────────────────

    @property
    def is_platform_admin(self) -> bool:
        """True only for PlatformAdmin — has full cross-org access."""
        return self.role == self.RoleChoices.PLATFORM_ADMIN

    @property
    def is_org_admin(self) -> bool:
        return self.role == self.RoleChoices.ORGANISATION_ADMIN

    @property
    def org_id(self) -> str | None:
        """
        Return the user's organisation pk as a string (for Firestore paths).
        Returns None for PlatformAdmin users who have no assigned org.
        """
        if self.organisation_id:
            return str(self.organisation_id)
        return None

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
