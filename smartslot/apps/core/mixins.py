"""Reusable mixins for SmartSlot core views."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


def is_platform_level(user):
    """
    Returns True for users with full platform-level (unscoped) access.
    Both Django superusers and users with the PlatformAdmin role are treated
    identically — they see all organisations with no data restrictions.
    """
    return bool(
        getattr(user, 'is_authenticated', False)
        and (
            getattr(user, 'is_superuser', False)
            or getattr(user, 'role', None) == 'PlatformAdmin'
        )
    )


def is_organisation_admin(user):
    """Return True when a user is scoped to a single organisation."""
    return bool(
        getattr(user, 'is_authenticated', False)
        and getattr(user, 'role', None) == 'OrganisationAdmin'
    )


def _normalise_org_key(value):
    return ''.join(ch for ch in (value or '').lower() if ch.isalnum())


def get_user_organisation(user):
    """
    Return an organisation admin's organisation.
    Older admin accounts may not have organisation_id set, so repair that link
    from their approved application email when possible.
    """
    if is_platform_level(user) or not is_organisation_admin(user):
        return None

    organisation = getattr(user, 'organisation', None)
    if organisation is not None:
        return organisation

    email = (getattr(user, 'email', '') or '').strip()
    if not email:
        return None

    from apps.core.models import Organisation, OrganisationApplication

    application = (
        OrganisationApplication.objects
        .filter(contact_email__iexact=email)
        .select_related('created_organisation')
        .order_by('-updated_at')
        .first()
    )
    organisation = application.created_organisation if application else None
    if organisation is None and application is not None:
        organisation = (
            Organisation.objects
            .filter(name__iexact=application.organisation_name)
            .order_by('-is_approved', '-updated_at')
            .first()
        )
    if organisation is None:
        email_local, _, email_domain = email.partition('@')
        domain_name = email_domain.split('.')[0] if email_domain else ''
        lookup_keys = {
            _normalise_org_key(getattr(user, 'username', '')),
            _normalise_org_key(email_local),
            _normalise_org_key(domain_name),
        }
        lookup_keys.discard('')
        lookup_keys.discard('admin')
        for org in Organisation.objects.all().order_by('name'):
            org_key = _normalise_org_key(org.name)
            if any(key in org_key or org_key in key for key in lookup_keys):
                organisation = org
                break
    if organisation is None:
        return None

    try:
        user.organisation = organisation
        user.save(update_fields=['organisation'])
    except Exception:
        pass
    return organisation


class OrgScopedMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restricts view access to OrganisationAdmin and PlatformAdmin roles.
    Provides scope_qs() to filter querysets to the user's organisation.

    PlatformAdmin → no restriction (sees all orgs).
    OrganisationAdmin → scoped to their own organisation.
    """
    login_url = '/dashboard/login/'

    def test_func(self):
        user = self.request.user
        return is_platform_level(user) or is_organisation_admin(user)

    def get_org(self):
        """Return the user's organisation, or None for platform-level users."""
        return get_user_organisation(self.request.user)

    def scope_qs(self, qs):
        """Filter queryset to the user's organisation if applicable."""
        org = self.get_org()
        if org is not None:
            return qs.filter(organisation=org)
        if is_organisation_admin(self.request.user):
            return qs.none()
        return qs
