"""
apps/core/models.py
-------------------
Core Django models (stored in SQLite):
  - Organisation  — one row per tenant; its pk is used as Firestore org_id
  - BaseModel     — abstract base inherited by all domain models

WHY keep Organisation in SQLite?
  Django's admin, auth, and session machinery need a relational database.
  Storing Organisation here means FK integrity is enforced by the DB engine,
  and the Django admin panel can manage orgs without any custom Firestore code.

  All *domain* data (resources, bookings, payments) lives in Firestore under
      organisations/{org_id}/...
  where {org_id} == str(Organisation.pk).
"""

from django.db import models


class Organisation(models.Model):
    """
    Represents a single tenant / client organisation.

    The primary key (auto-assigned integer) doubles as the Firestore
    document ID in the  organisations/{org_id}  path, so always pass
    str(organisation.pk)  when building Firestore references.
    """

    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='organisation_logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self):
        return self.name

    @property
    def firestore_id(self) -> str:
        """Convenience: return pk as a string for use in Firestore paths."""
        return str(self.pk)


class BaseModel(models.Model):
    """
    Abstract base for all domain models that belong to an Organisation.

    Fields
    ------
    organisation : FK → Organisation
        Every record is scoped to exactly one organisation.
        The column is used for Django admin filtering and FK integrity;
        in Firestore the same scoping is done by the collection path.
    created_at / updated_at : auto timestamps
    """

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
