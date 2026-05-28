from django.db import migrations


class Migration(migrations.Migration):
    """Merge the two divergent 0008 leaf migrations."""

    dependencies = [
        ('resources', '0008_alter_resource_is_active'),
        ('resources', '0008_resource_db_photo_fields'),
    ]

    operations = []
