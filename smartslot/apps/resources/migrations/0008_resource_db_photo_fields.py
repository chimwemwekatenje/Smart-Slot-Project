from django.db import migrations, models


def add_db_photo_fields(apps, schema_editor):
    Resource = apps.get_model('resources', 'Resource')
    table = Resource._meta.db_table
    cursor = schema_editor.connection.cursor()
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            cursor,
            table,
        )
    }

    if 'photo_data' not in existing_columns:
        schema_editor.execute(
            f"ALTER TABLE {schema_editor.quote_name(table)} "
            f"ADD COLUMN {schema_editor.quote_name('photo_data')} text NOT NULL DEFAULT ''"
        )

    if 'photo_mime' not in existing_columns:
        schema_editor.execute(
            f"ALTER TABLE {schema_editor.quote_name(table)} "
            f"ADD COLUMN {schema_editor.quote_name('photo_mime')} varchar(100) NOT NULL DEFAULT ''"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0007_merge_20260528_0057'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_db_photo_fields, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='resource',
                    name='photo_data',
                    field=models.TextField(blank=True),
                ),
                migrations.AddField(
                    model_name='resource',
                    name='photo_mime',
                    field=models.CharField(blank=True, max_length=100),
                ),
            ],
        ),
    ]
