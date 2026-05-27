from django.db import migrations
from django.utils import timezone


def activate_existing_resources(apps, schema_editor):
    Organisation = apps.get_model('core', 'Organisation')
    Resource = apps.get_model('resources', 'Resource')

    now = timezone.now()
    Organisation.objects.filter(is_approved=False).update(
        is_approved=True,
        approved_at=now,
    )
    Resource.objects.filter(is_active=False).update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_organisation_approved_at_organisation_is_approved'),
        ('resources', '0005_resource_is_active_alter_resource_image_url'),
    ]

    operations = [
        migrations.RunPython(activate_existing_resources, migrations.RunPython.noop),
    ]
