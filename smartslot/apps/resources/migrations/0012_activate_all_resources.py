from django.db import migrations


def activate_all_resources(apps, schema_editor):
    Resource = apps.get_model('resources', 'Resource')
    Resource.objects.filter(is_active=False).update(is_active=True)


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0011_resource_category_choices'),
    ]

    operations = [
        migrations.RunPython(activate_all_resources, migrations.RunPython.noop),
    ]
