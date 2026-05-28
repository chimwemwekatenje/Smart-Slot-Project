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

    from apps.core.models import OrganisationApplication

    application = (
        OrganisationApplication.objects
        .filter(contact_email__iexact=email)
        .select_related('created_organisation')
        .order_by('-updated_at')
        .first()
    )
    if not application:
        return None

    organisation = application.created_organisation
    if organisation is None:
        from apps.core.models import Organisation
        organisation = (
            Organisation.objects
            .filter(name__iexact=application.organisation_name)
            .order_by('-is_approved', '-updated_at')
            .first()
        )
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
