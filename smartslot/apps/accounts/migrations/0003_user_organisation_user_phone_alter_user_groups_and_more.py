# Compatibility migration kept for deployments that already saw this filename.
#
# The fields in the original generated migration are already represented by:
# - 0003_add_organisation_to_user
# - 0004_user_phone
#
# Leaving duplicate AddField operations here breaks fresh deploys, and the
# original dependency pointed at a migration that is not in this repository.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_phone'),
    ]

    operations = []
