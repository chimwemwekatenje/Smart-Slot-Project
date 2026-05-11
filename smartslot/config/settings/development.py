from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '*']

# Use a local SQLite database for development so the server works
# offline and without needing a live Supabase connection.
# Switch back to the Supabase DATABASE_URL only for staging/production.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Override SITE_URL in .env with your machine's LAN IP when testing on phone.
# e.g. SITE_URL=http://192.168.1.42:8000
# Leave unset to use the default http://127.0.0.1:8000