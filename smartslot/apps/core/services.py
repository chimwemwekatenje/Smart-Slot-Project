"""
apps/core/services.py
---------------------
Shared helpers that enforce multi-tenant access rules.

The one golden rule
-------------------
  - PlatformAdmin  → no restriction; can access any organisation.
  - Everyone else  → restricted to the organisation stored on their user row.

Import this in any view or service that needs to know "which org does the
current user belong to?".
"""

from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model

User = get_user_model()


def get_org_id_for_user(user) -> int | None:
    """
    Return the organisation ID (integer PK) for *user*.

    Parameters
    ----------
    user : accounts.User
        The currently logged-in user (request.user).

    Returns
    -------
    int or None
        The organisation primary key, or None for PlatformAdmins
        (signal meaning "no restriction — access all orgs").

    Raises
    ------
    PermissionDenied
        If the user is not a PlatformAdmin and has no organisation assigned.
        This prevents accidental cross-tenant data access.
    """
    # PlatformAdmin is never restricted — callers must handle None specially
    if user.is_platform_admin:
        return None  # signal: "no restriction"

    if not user.org_id:
        raise PermissionDenied(
            f"User '{user.username}' has no organisation assigned. "
            "Contact your Platform Administrator."
        )

    return user.org_id


def assert_same_org(user, org_id: int) -> None:
    """
    Raise PermissionDenied unless *user* belongs to *org_id* (or is a
    PlatformAdmin).

    Use this when you already have an org_id from a URL parameter or a
    database record and need to verify the user is allowed to see it.

    Parameters
    ----------
    user : accounts.User
    org_id : int
        The organisation ID taken from the resource/booking being accessed.
    """
    if user.is_platform_admin:
        return  # full access

    user_org = get_org_id_for_user(user)
    if user_org != int(org_id):
        raise PermissionDenied(
            "You do not have permission to access data from this organisation."
        )
