from django.db import migrations


class Migration(migrations.Migration):
    """Merge the historical 0006 branch with the later 0005 merge marker."""

    dependencies = [
        ('core', '0005_merge_core_0004s'),
        ('core', '0006_merge_20260528_0406'),
    ]

    operations = []
