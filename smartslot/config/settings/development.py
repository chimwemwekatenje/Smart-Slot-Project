from .base import *
from django.core.exceptions import ImproperlyConfigured

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '*']

# Local development uses the same Supabase Postgres database as production.
# Set DATABASE_URL in smartslot/.env to your Supabase connection string.
if not env('DATABASE_URL', default=''):
    raise ImproperlyConfigured(
        'DATABASE_URL is required in development. Add your Supabase Postgres '
        'connection string to smartslot/.env.'
    )

DATABASES = {
    'default': env.db('DATABASE_URL'),
}

# Supabase requires SSL for Postgres connections unless explicitly disabled
# in the project settings. Preserve sslmode if it is already in DATABASE_URL.
DATABASES['default'].setdefault('OPTIONS', {})
DATABASES['default']['OPTIONS'].setdefault('sslmode', 'require')
