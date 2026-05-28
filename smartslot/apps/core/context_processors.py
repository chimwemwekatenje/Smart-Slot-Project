from django.conf import settings


def site_url(request):
    """Expose SITE_URL to all templates so QR codes and absolute links work
    correctly in both local dev and production."""
    return {'SITE_URL': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}


def dashboard_organisation(request):
    """Expose the resolved organisation for organisation-admin dashboard chrome."""
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return {'dashboard_organisation': None}
    try:
        from apps.core.mixins import get_user_organisation
        return {'dashboard_organisation': get_user_organisation(user)}
    except Exception:
        return {'dashboard_organisation': getattr(user, 'organisation', None)}
