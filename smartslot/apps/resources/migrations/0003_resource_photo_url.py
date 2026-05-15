from django.db import migrations, models


class Migration(migrations.Migration):
    """Adds photo_url to store the permanent Supabase Storage public URL."""

    dependencies = [
        ('resources', '0002_resource_image_url_alter_resource_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='photo_url',
            field=models.URLField(blank=True, max_length=600, null=True),
        ),
    ]
