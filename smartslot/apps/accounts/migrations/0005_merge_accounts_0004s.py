from django.db import migrations


class Migration(migrations.Migration):
    """Merge the two divergent 0004 leaf migrations in accounts."""

    dependencies = [
        ('accounts', '0004_alter_user_role'),
        ('accounts', '0004_user_phone'),
    ]

    operations = []
