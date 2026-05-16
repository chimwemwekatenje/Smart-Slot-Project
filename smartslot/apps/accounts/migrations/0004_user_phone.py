from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_organisation_to_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
