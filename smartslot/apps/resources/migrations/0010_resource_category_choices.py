"""
Two-step migration for the Resource.category field:

Step 1 (data)  — normalise every existing category value to the canonical
                 capitalised form before the choices constraint is applied.
Step 2 (schema)— add choices= to the field so Django validates new values.

The normalisation map is intentionally broad so it handles common variants
found in the wild (all-lowercase, all-uppercase, with/without spaces, etc.).
Any value that doesn't match a known variant is left as-is so no data is
silently lost; it will simply fail the new choices validation if someone
tries to save it again, prompting a manual fix.
"""

from django.db import migrations, models


# ── Canonical choices (must match Resource.CategoryChoices exactly) ──────────
CANONICAL = [
    'Boardroom',
    'Equipment',
    'Vehicle',
    'Workspace',
    'IT & Technology',
    'Facility',
    'Catering',
    'Other',
]

# Map every known variant → canonical value (case-insensitive lookup below)
_NORMALISE_MAP = {
    # Boardroom
    'boardroom':  'Boardroom',
    'board room': 'Boardroom',
    'meeting room': 'Boardroom',
    'conference room': 'Boardroom',
    # Equipment
    'equipment':  'Equipment',
    'equipments': 'Equipment',
    'gear':       'Equipment',
    # Vehicle
    'vehicle':    'Vehicle',
    'vehicles':   'Vehicle',
    'car':        'Vehicle',
    'transport':  'Vehicle',
    # Workspace
    'workspace':  'Workspace',
    'work space': 'Workspace',
    'desk':       'Workspace',
    'office':     'Workspace',
    # IT & Technology
    'it & technology': 'IT & Technology',
    'it':              'IT & Technology',
    'technology':      'IT & Technology',
    'tech':            'IT & Technology',
    'it equipment':    'IT & Technology',
    # Facility
    'facility':   'Facility',
    'facilities': 'Facility',
    'room':       'Facility',
    # Catering
    'catering':   'Catering',
    'food':       'Catering',
    'kitchen':    'Catering',
    # Other
    'other':      'Other',
    'misc':       'Other',
    'miscellaneous': 'Other',
    # Legacy seed-data values that don't map to the new list
    'training room': 'Workspace',
    'event venue':   'Facility',
}


def normalise_categories(apps, schema_editor):
    """Rewrite every Resource.category to its canonical form."""
    Resource = apps.get_model('resources', 'Resource')
    for resource in Resource.objects.all():
        canonical = _NORMALISE_MAP.get(resource.category.strip().lower())
        if canonical and resource.category != canonical:
            resource.category = canonical
            resource.save(update_fields=['category'])


def reverse_normalise(apps, schema_editor):
    """No-op reverse — we can't recover the original mixed-case values."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_merge_0008s'),
    ]

    operations = [
        # Step 1: normalise existing data BEFORE the choices constraint lands
        migrations.RunPython(normalise_categories, reverse_normalise),

        # Step 2: add choices= to the field (schema-only, no DB column change)
        migrations.AlterField(
            model_name='resource',
            name='category',
            field=models.CharField(
                max_length=255,
                choices=[
                    ('Boardroom',      'Boardroom'),
                    ('Equipment',      'Equipment'),
                    ('Vehicle',        'Vehicle'),
                    ('Workspace',      'Workspace'),
                    ('IT & Technology','IT & Technology'),
                    ('Facility',       'Facility'),
                    ('Catering',       'Catering'),
                    ('Other',          'Other'),
                ],
            ),
        ),
    ]
