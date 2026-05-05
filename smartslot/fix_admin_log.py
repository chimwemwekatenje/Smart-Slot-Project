"""
Run with: python fix_admin_log.py
Fixes the django_admin_log.user_id type mismatch (uuid vs bigint).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection

print("Fixing django_admin_log.user_id column type...")

with connection.cursor() as cursor:
    # Clear existing log entries (they reference old uuid users anyway)
    cursor.execute("DELETE FROM django_admin_log;")
    print("Cleared old admin log entries.")

    # Drop the old foreign key constraint
    cursor.execute("""
        ALTER TABLE django_admin_log
        DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_profiles_id;
    """)
    print("Dropped old FK constraint.")

    # Change the column type from uuid to bigint
    cursor.execute("""
        ALTER TABLE django_admin_log
        ALTER COLUMN user_id TYPE bigint USING 0;
    """)
    print("Changed user_id to bigint.")

    # Add new FK constraint pointing to accounts_user
    cursor.execute("""
        ALTER TABLE django_admin_log
        ADD CONSTRAINT django_admin_log_user_id_fk
        FOREIGN KEY (user_id) REFERENCES accounts_user(id)
        DEFERRABLE INITIALLY DEFERRED;
    """)
    print("Added new FK constraint to accounts_user.")

print("Done! Admin panel should work now.")
