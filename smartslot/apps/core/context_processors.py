from django.conf import settings


def site_url(request):
    """Expose SITE_URL to all templates so QR codes and absolute links work
    correctly in both local dev and production."""
    return {'SITE_URL': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}
