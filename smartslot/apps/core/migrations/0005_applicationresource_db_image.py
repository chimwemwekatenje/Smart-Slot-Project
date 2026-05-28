from django.db import migrations, models


def add_db_image_fields(apps, schema_editor):
    ApplicationResource = apps.get_model('core', 'ApplicationResource')
    table = ApplicationResource._meta.db_table
    cursor = schema_editor.connection.cursor()
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            cursor,
            table,
        )
    }

    if 'image_data' not in existing_columns:
        schema_editor.execute(
            f"ALTER TABLE {schema_editor.quote_name(table)} "
            f"ADD COLUMN {schema_editor.quote_name('image_data')} text NOT NULL DEFAULT ''"
        )

    if 'image_mime' not in existing_columns:
        schema_editor.execute(
            f"ALTER TABLE {schema_editor.quote_name(table)} "
            f"ADD COLUMN {schema_editor.quote_name('image_mime')} varchar(100) NOT NULL DEFAULT ''"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_merge_20260528_0057'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_db_image_fields, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='applicationresource',
                    name='image_data',
                    field=models.TextField(blank=True),
                ),
                migrations.AddField(
                    model_name='applicationresource',
                    name='image_mime',
                    field=models.CharField(blank=True, max_length=100),
                ),
                migrations.RemoveField(
                    model_name='applicationresource',
                    name='image',
                ),
            ],
        ),
    ]
