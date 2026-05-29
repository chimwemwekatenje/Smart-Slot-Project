#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.resources.models import Resource

resources = Resource.objects.filter(id__in=[1, 2, 11])
for r in resources:
    has_photo = bool(r.photo)
    photo_url = r.photo.url if has_photo else "No photo"
    print(f"Resource {r.id} ({r.name}): {photo_url}")
