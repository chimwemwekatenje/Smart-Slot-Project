from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Increases price precision from max_digits=10 to max_digits=14
    so values up to 999,999,999,999.99 are accepted.
    """

    dependencies = [
        ('resources', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=14),
        ),
    ]
