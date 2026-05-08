"""Reusable mixins for SmartSlot core views."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class OrgScopedMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restricts view access to OrganisationAdmin and PlatformAdmin roles.
    Provides scope_qs() to filter querysets to the user's organisation.

    PlatformAdmin → no restriction (sees all orgs).
    OrganisationAdmin → scoped to their own organisation.
    """
    login_url = '/dashboard/login/'

    def test_func(self):
        return self.request.user.role in ('OrganisationAdmin', 'PlatformAdmin')

    def get_org(self):
        """Return the user's organisation, or None for PlatformAdmin."""
        user = self.request.user
        if user.role == 'PlatformAdmin' or user.is_superuser:
            return None
        return user.organisation

    def scope_qs(self, qs):
        """Filter queryset to the user's organisation if applicable."""
        org = self.get_org()
        if org is not None:
            return qs.filter(organisation=org)
        return qs
