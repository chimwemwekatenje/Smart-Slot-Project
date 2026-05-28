from django.db import migrations


class Migration(migrations.Migration):
    """Merge the two divergent 0004 leaf migrations in core."""

    dependencies = [
        ('core', '0004_merge_20260528_0057'),
        ('core', '0004_merge_20260528_0159'),
    ]

    operations = []
