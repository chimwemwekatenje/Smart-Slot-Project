import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        SUPER_ADMIN       = 'super_admin',      'Super Admin'
        ORG_ADMIN         = 'org_admin',        'Organisation Admin'
        EMPLOYEE          = 'employee',         'Employee'
        EXTERNAL          = 'external',         'External'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Custom fields mapping to 'profiles' table
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.EMPLOYEE,
    )
    organisation = models.ForeignKey(
        'core.Organisation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'profiles'
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    @property
    def is_platform_admin(self) -> bool:
        """True only for super_admin â€” has full cross-org access."""
        return self.role == self.RoleChoices.SUPER_ADMIN

    @property
    def is_org_admin(self) -> bool:
        return self.role == self.RoleChoices.ORG_ADMIN

    @property
    def org_id(self) -> str | None:
        """Return the user's organisation pk (UUID as string)."""
        return str(self.organisation_id) if self.organisation_id else None

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
