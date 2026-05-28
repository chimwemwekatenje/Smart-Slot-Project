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
        user = self.request.user
        if is_platform_level(user):
            return None
        return getattr(user, 'organisation', None)

    def scope_qs(self, qs):
        """Filter queryset to the user's organisation if applicable."""
        org = self.get_org()
        if org is not None:
            return qs.filter(organisation=org)
        if is_organisation_admin(self.request.user):
            return qs.none()
        return qs
