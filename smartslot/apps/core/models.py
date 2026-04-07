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
