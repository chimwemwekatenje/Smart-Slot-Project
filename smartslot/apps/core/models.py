import uuid
from django.db import models


class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tier_name = models.CharField(max_length=50, unique=True)
    max_resources = models.IntegerField()
    max_users = models.IntegerField()
    monthly_price_mwk = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    supports_payments = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subscription_plans'
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"

    def __str__(self):
        return self.tier_name


class Organisation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    TIER_CHOICES = [
        ('free', 'Free'),
        ('sme', 'SME'),
        ('enterprise', 'Enterprise'),
    ]
    subscription_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organisations'
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self):
        return self.name


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
