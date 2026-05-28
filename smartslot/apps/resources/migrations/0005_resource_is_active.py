from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0004_merge_0002_resource_image_url_0003_resource_photo_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='is_active',
            field=models.BooleanField(
                default=False,
                help_text='Activated automatically when the parent organisation is approved.',
            ),
        ),
    ]
