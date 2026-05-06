from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']

# Use a local SQLite database for development so the server works
# offline and without needing a live Supabase connection.
# Switch back to the Supabase DATABASE_URL only for staging/production.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}