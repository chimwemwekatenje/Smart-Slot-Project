from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0006_simplify_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(
                choices=[
                    ('Pending', 'Pending'),
                    ('Booked', 'Booked'),
                    ('Cancelled', 'Cancelled'),
                ],
                default='Booked',
                max_length=20,
            ),
        ),
    ]
