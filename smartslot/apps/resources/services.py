"""
apps/resources/services.py
--------------------------
All Firestore operations for the Resources domain.

Every function takes an  organisation_id  parameter.  Views must obtain
this value from  apps.core.services.get_org_id_for_user(request.user)
before calling anything here.

Firestore path
--------------
    organisations/{org_id}/resources/{resource_id}

Document schema
---------------
    {
        "name":          str,
        "description":   str,
        "category":      str,
        "price":         float,
        "photo_url":     str | None,
        "custom_fields": dict,
        "created_by":    str,   # username of the creating user
        "organisation_id": str, # denormalised for safety
    }
"""

import logging
from apps.core.firebase import org_collection

logger = logging.getLogger(__name__)

# ── Firestore collection shortcut ────────────────────────────────────────────

def _resources_col(organisation_id: str):
    """Return the Firestore collection ref for this org's resources."""
    return org_collection(organisation_id, 'resources')


# ── Read operations ──────────────────────────────────────────────────────────

def get_resources_for_organisation(organisation_id: str) -> list[dict]:
    """
    Return all resources that belong to *organisation_id*.

    Parameters
    ----------
    organisation_id : str
        The pk of the Organisation (as a string).

    Returns
    -------
    list of dict
        Each dict has all document fields plus an 'id' key (Firestore doc ID).
    """
    col = _resources_col(organisation_id)
    docs = col.stream()
    resources = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        resources.append(data)
    logger.debug("Fetched %d resources for org %s", len(resources), organisation_id)
    return resources


def get_resource_by_id(organisation_id: str, resource_id: str) -> dict | None:
    """
    Return a single resource document, or None if it does not exist.

    Also verifies that the document's  organisation_id  field matches the
    expected value — this prevents ID-guessing attacks across tenants.

    Parameters
    ----------
    organisation_id : str
    resource_id : str
        The Firestore document ID.
    """
    doc = _resources_col(organisation_id).document(resource_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    # Safety check: doc must belong to the expected org
    if data.get('organisation_id') != str(organisation_id):
        logger.warning(
            "Resource %s claims org %s but was fetched under org %s — denied.",
            resource_id, data.get('organisation_id'), organisation_id,
        )
        return None
    data['id'] = doc.id
    return data


def get_all_resources() -> list[dict]:
    """
    Return resources from ALL organisations.

    This may only be called by PlatformAdmin users; the view layer is
    responsible for enforcing that rule before calling this function.
    """
    from apps.core.firebase import get_firestore_client
    db = get_firestore_client()
    # Firestore collection group query across all orgs
    docs = db.collection_group('resources').stream()
    resources = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        resources.append(data)
    logger.debug("PlatformAdmin: fetched %d resources across all orgs", len(resources))
    return resources


def search_resources(organisation_id: str, query: str = '', category: str = '') -> list[dict]:
    """
    Filter resources by name substring and/or category.

    Note: Firestore does not support server-side ILIKE; filtering is done
    in Python after fetching all documents for the organisation.

    Parameters
    ----------
    organisation_id : str
    query : str
        Case-insensitive substring match on the 'name' field.
    category : str
        Exact match on the 'category' field.  Pass '' to skip.
    """
    resources = get_resources_for_organisation(organisation_id)
    if query:
        q = query.lower()
        resources = [r for r in resources if q in r.get('name', '').lower()]
    if category and category != 'All':
        resources = [r for r in resources if r.get('category') == category]
    return resources


def get_categories_for_organisation(organisation_id: str) -> list[str]:
    """Return a sorted list of unique category values for the organisation."""
    resources = get_resources_for_organisation(organisation_id)
    cats = sorted({r.get('category', '') for r in resources if r.get('category')})
    return cats


# ── Write operations ─────────────────────────────────────────────────────────

def create_resource(organisation_id: str, data: dict, created_by: str = '') -> str:
    """
    Create a new resource document in Firestore.

    Parameters
    ----------
    organisation_id : str
    data : dict
        Must contain at least: name, category.
        Optional: description, price, photo_url, custom_fields.
    created_by : str
        Username of the user creating this resource (for audit trail).

    Returns
    -------
    str
        The Firestore document ID of the newly created resource.
    """
    payload = {
        'name':            data.get('name', ''),
        'description':     data.get('description', ''),
        'category':        data.get('category', ''),
        'price':           float(data.get('price', 0)),
        'photo_url':       data.get('photo_url'),
        'custom_fields':   data.get('custom_fields', {}),
        'created_by':      created_by,
        'organisation_id': str(organisation_id),  # denormalised safety field
    }
    _, doc_ref = _resources_col(organisation_id).add(payload)
    logger.info("Created resource %s for org %s by %s", doc_ref.id, organisation_id, created_by)
    return doc_ref.id


def update_resource(organisation_id: str, resource_id: str, data: dict) -> None:
    """
    Update specific fields of an existing resource document.

    Parameters
    ----------
    organisation_id : str
    resource_id : str
    data : dict
        Only the key/value pairs you want to change.
    """
    # Never allow changing the organisation via an update
    data.pop('organisation_id', None)
    _resources_col(organisation_id).document(resource_id).update(data)
    logger.info("Updated resource %s in org %s", resource_id, organisation_id)


def delete_resource(organisation_id: str, resource_id: str) -> None:
    """
    Delete a resource document.

    Parameters
    ----------
    organisation_id : str
    resource_id : str
    """
    _resources_col(organisation_id).document(resource_id).delete()
    logger.info("Deleted resource %s from org %s", resource_id, organisation_id)
