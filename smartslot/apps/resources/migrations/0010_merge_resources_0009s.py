from django.db import migrations


class Migration(migrations.Migration):
    """Merge the two divergent 0009 leaf migrations in resources."""

    dependencies = [
        ('resources', '0009_merge_0008s'),
        ('resources', '0009_merge_20260528_0406'),
    ]

    operations = []
