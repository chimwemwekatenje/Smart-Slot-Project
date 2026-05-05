"""
Run this with: python fix_db.py
Creates the accounts_user table then runs all migrations.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection

print("Connecting to database...")

with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts_user (
            id bigserial PRIMARY KEY,
            password varchar(128) NOT NULL,
            last_login timestamptz,
            is_superuser boolean NOT NULL DEFAULT false,
            username varchar(150) NOT NULL UNIQUE,
            first_name varchar(150) NOT NULL DEFAULT '',
            last_name varchar(150) NOT NULL DEFAULT '',
            email varchar(254) NOT NULL DEFAULT '',
            is_staff boolean NOT NULL DEFAULT false,
            is_active boolean NOT NULL DEFAULT true,
            date_joined timestamptz NOT NULL DEFAULT now(),
            role varchar(20) NOT NULL DEFAULT 'Employee'
        );
    """)
    print("accounts_user table created.")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts_user_groups (
            id bigserial PRIMARY KEY,
            user_id bigint NOT NULL REFERENCES accounts_user(id),
            group_id integer NOT NULL REFERENCES auth_group(id)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts_user_user_permissions (
            id bigserial PRIMARY KEY,
            user_id bigint NOT NULL REFERENCES accounts_user(id),
            permission_id integer NOT NULL REFERENCES auth_permission(id)
        );
    """)
    print("accounts_user_groups and accounts_user_user_permissions created.")

print("Done! Now run: python manage.py migrate")
