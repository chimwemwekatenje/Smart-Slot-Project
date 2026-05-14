import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

# =============================================================================
# Core Django
# =============================================================================
SECRET_KEY = env('SECRET_KEY', default='unsafe-secret-key')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'crispy_forms',
    'crispy_tailwind',
    # Local apps - core MUST be first (BaseModel / Organisation FK dependency)
    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.resources.apps.ResourcesConfig',
    'apps.bookings.apps.BookingsConfig',
    'apps.payments.apps.PaymentsConfig',
    'apps.verification.apps.VerificationConfig',
]

AUTH_USER_MODEL = 'accounts.User'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_url',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# =============================================================================
# Database
# =============================================================================
# Reads DATABASE_URL from .env.
#
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}


DATABASES['default']['CONN_MAX_AGE'] = 60


DATABASES['default']['CONN_HEALTH_CHECKS'] = True

# Required for Supabase / any hosted Postgres — enforce SSL.
DATABASES['default'].setdefault('OPTIONS', {})
DATABASES['default']['OPTIONS']['sslmode'] = 'require'
# =============================================================================
# Auth & Password
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# Internationalisation
# =============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# Static & Media
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/resources/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Site URL — used for QR codes, emails, and any absolute URLs.
# Set SITE_URL in your .env for local dev (e.g. http://192.168.x.x:8000)
# and in production env vars (e.g. https://smartslot-bh9c.onrender.com).
SITE_URL = env('SITE_URL', default='https://smartslot-bh9c.onrender.com')

# PayChangu
# =============================================================================
PAYCHANGU_SECRET_KEY = env('PAYCHANGU_SECRET_KEY', default='')
PAYCHANGU_CALLBACK_URL = env('PAYCHANGU_CALLBACK_URL', default='http://127.0.0.1:8000/payments/callback/')
PAYCHANGU_RETURN_URL = env('PAYCHANGU_RETURN_URL', default='http://127.0.0.1:8000/payments/return/')
