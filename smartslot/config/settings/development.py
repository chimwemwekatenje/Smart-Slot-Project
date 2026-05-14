from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '*']

# Database comes from DATABASE_URL in .env — same Supabase instance as production.
# This means users, bookings, and resources created locally are immediately
# visible on the deployed site and vice versa.
#
# If you ever need a fully offline/isolated local DB, comment the line above
# and uncomment this block:
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
