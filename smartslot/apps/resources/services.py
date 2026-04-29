"""
apps/resources/services.py
--------------------------
All database operations for the Resources domain — now using the Django ORM
backed by Supabase PostgreSQL.

Every function accepts an organisation_id (int) parameter. Views obtain this
value from apps.core.services.get_org_id_for_user(request.user) before
calling anything here.

The service layer returns plain Python dicts (mirroring the old Firestore API)
so that views and templates require minimal changes.
"""

import logging
from apps.resources.models import Resource

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _qs_to_dict(qs) -> list[dict]:
    """Convert a Resource queryset to a list of dicts (consistent with old API)."""
    result = []
    for r in qs:
        result.append({
            'id':            r.pk,
            'name':          r.name,
            'description':   r.description,
            'category':      r.category,
            'price':         float(r.price),
            'photo_url':     r.photo.url if r.photo else None,
            'custom_fields': r.custom_fields,
            'organisation_id': r.organisation_id,
        })
    return result


# ── Read operations ───────────────────────────────────────────────────────────

def get_resources_for_organisation(organisation_id: int) -> list[dict]:
    """
    Return all resources that belong to *organisation_id*.

    Parameters
    ----------
    organisation_id : int

    Returns
    -------
    list of dict
    """
    qs = Resource.objects.filter(organisation_id=organisation_id).order_by('name')
    logger.debug("Fetched %d resources for org %s", qs.count(), organisation_id)
    return _qs_to_dict(qs)


def get_resource_by_id(organisation_id: int, resource_id: int) -> dict | None:
    """
    Return a single resource dict, or None if it doesn't exist or belongs
    to a different organisation (prevents cross-tenant access).

    Parameters
    ----------
    organisation_id : int
    resource_id : int
    """
    try:
        r = Resource.objects.get(pk=resource_id, organisation_id=organisation_id)
    except Resource.DoesNotExist:
        return None
    return _qs_to_dict([r])[0]


def get_all_resources() -> list[dict]:
    """
    Return resources from ALL organisations.

    This may only be called by PlatformAdmin users; the view layer is
    responsible for enforcing that rule before calling this function.
    """
    qs = Resource.objects.select_related('organisation').order_by('organisation', 'name')
    logger.debug("PlatformAdmin: fetched %d resources across all orgs", qs.count())
    return _qs_to_dict(qs)


def search_resources(organisation_id: int, query: str = '', category: str = '') -> list[dict]:
    """
    Filter resources by name substring and/or category.

    Parameters
    ----------
    organisation_id : int
    query : str
        Case-insensitive substring match on the 'name' field.
    category : str
        Exact match on the 'category' field. Pass '' to skip.
    """
    qs = Resource.objects.filter(organisation_id=organisation_id)
    if query:
        qs = qs.filter(name__icontains=query)
    if category and category != 'All':
        qs = qs.filter(category=category)
    return _qs_to_dict(qs.order_by('name'))


def get_categories_for_organisation(organisation_id: int) -> list[str]:
    """Return a sorted list of unique category values for the organisation."""
    cats = (
        Resource.objects
        .filter(organisation_id=organisation_id)
        .exclude(category='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )
    return list(cats)


# ── Write operations ──────────────────────────────────────────────────────────

def create_resource(organisation_id: int, data: dict, created_by: str = '') -> int:
    """
    Create a new Resource row.

    Parameters
    ----------
    organisation_id : int
    data : dict
        Must contain at least: name, category.
        Optional: description, price, photo_url, custom_fields.
    created_by : str
        Username of the user creating this resource (for audit trail).

    Returns
    -------
    int
        The PK of the newly created Resource.
    """
    resource = Resource.objects.create(
        organisation_id=organisation_id,
        name=data.get('name', ''),
        description=data.get('description', ''),
        category=data.get('category', ''),
        price=data.get('price', 0),
        custom_fields=data.get('custom_fields', {}),
    )
    logger.info("Created resource %s for org %s by %s", resource.pk, organisation_id, created_by)
    return resource.pk


def update_resource(organisation_id: int, resource_id: int, data: dict) -> None:
    """
    Update specific fields of an existing resource.

    Parameters
    ----------
    organisation_id : int
    resource_id : int
    data : dict
        Only the key/value pairs you want to change.
    """
    # Never allow changing the organisation via an update
    data.pop('organisation_id', None)
    data.pop('organisation', None)

    Resource.objects.filter(pk=resource_id, organisation_id=organisation_id).update(**data)
    logger.info("Updated resource %s in org %s", resource_id, organisation_id)


def delete_resource(organisation_id: int, resource_id: int) -> None:
    """
    Delete a resource.

    Parameters
    ----------
    organisation_id : int
    resource_id : int
    """
    Resource.objects.filter(pk=resource_id, organisation_id=organisation_id).delete()
    logger.info("Deleted resource %s from org %s", resource_id, organisation_id)
