from .base import *
import os

# Always False in production — never read from env
DEBUG = False

# Hardcoded so this never falls back to base defaults regardless of env vars
ALLOWED_HOSTS = [
    'smartslot-bh9c.onrender.com',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'https://smartslot-bh9c.onrender.com',
]

# Absolute site URL — used for QR codes and any absolute links in emails/PDFs
SITE_URL = 'https://smartslot-bh9c.onrender.com'

# Static files served by WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
