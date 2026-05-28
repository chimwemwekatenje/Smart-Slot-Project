"""
Two-step migration for the Resource.category field:

Step 1 (data)  — normalise every existing category value to the canonical
                 capitalised form before the choices constraint is applied.
Step 2 (schema)— add choices= to the field so Django validates new values.
"""

from django.db import migrations, models

_NORMALISE_MAP = {
    'boardroom':       'Boardroom',
    'board room':      'Boardroom',
    'meeting room':    'Boardroom',
    'conference room': 'Boardroom',
    'equipment':       'Equipment',
    'equipments':      'Equipment',
    'gear':            'Equipment',
    'vehicle':         'Vehicle',
    'vehicles':        'Vehicle',
    'car':             'Vehicle',
    'transport':       'Vehicle',
    'workspace':       'Workspace',
    'work space':      'Workspace',
    'desk':            'Workspace',
    'office':          'Workspace',
    'it & technology': 'IT & Technology',
    'it':              'IT & Technology',
    'technology':      'IT & Technology',
    'tech':            'IT & Technology',
    'it equipment':    'IT & Technology',
    'facility':        'Facility',
    'facilities':      'Facility',
    'room':            'Facility',
    'catering':        'Catering',
    'food':            'Catering',
    'kitchen':         'Catering',
    'other':           'Other',
    'misc':            'Other',
    'miscellaneous':   'Other',
    'training room':   'Workspace',
    'event venue':     'Facility',
}


def normalise_categories(apps, schema_editor):
    Resource = apps.get_model('resources', 'Resource')
    for resource in Resource.objects.all():
        canonical = _NORMALISE_MAP.get(resource.category.strip().lower())
        if canonical and resource.category != canonical:
            resource.category = canonical
            resource.save(update_fields=['category'])


def reverse_normalise(apps, schema_editor):
    pass  # irreversible — original mixed-case values are gone


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0010_merge_resources_0009s'),
    ]

    operations = [
        migrations.RunPython(normalise_categories, reverse_normalise),
        migrations.AlterField(
            model_name='resource',
            name='category',
            field=models.CharField(
                max_length=255,
                choices=[
                    ('Boardroom',       'Boardroom'),
                    ('Equipment',       'Equipment'),
                    ('Vehicle',         'Vehicle'),
                    ('Workspace',       'Workspace'),
                    ('IT & Technology', 'IT & Technology'),
                    ('Facility',        'Facility'),
                    ('Catering',        'Catering'),
                    ('Other',           'Other'),
                ],
            ),
        ),
    ]
