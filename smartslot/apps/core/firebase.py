"""
apps/core/firebase.py
---------------------
Single entry-point for all Firestore access in SmartSlot.

Quick-start for any app
-----------------------
    from apps.core.firebase import get_firestore_client

    db = get_firestore_client()
    if db is None:
        # Firebase not ready — handle gracefully
        ...

    # Write a document
    db.collection('resources').document('some-id').set({...})

    # Read documents
    for doc in db.collection('resources').stream():
        print(doc.id, doc.to_dict())

Firestore collection layout
----------------------------
    organisations/{org_id}/resources/{resource_id}
    organisations/{org_id}/bookings/{booking_id}
    organisations/{org_id}/users/{user_id}        (optional mirror)

    The {org_id} always matches the Django Organisation.pk (as a string).
"""

import logging
import firebase_admin
from firebase_admin import firestore

logger = logging.getLogger(__name__)

# ── Singleton cache ───────────────────────────────────────────────────────────
# Stored at module level so the Firestore gRPC connection is reused across
# every request in the same Django process (WSGI/ASGI worker).
_firestore_client = None


def get_firestore_client():
    """
    Return a ready-to-use Firestore client.

    The client is created once per process and cached.  Subsequent calls
    return the cached instance immediately without any I/O.

    Returns
    -------
    google.cloud.firestore.Client
        A connected Firestore client.

    Raises
    ------
    RuntimeError
        If the Firebase app has not been initialized yet (i.e. Django
        settings have not been loaded).  This should never happen in normal
        operation because base.py calls firebase_admin.initialize_app()
        at import time.
    """
    global _firestore_client

    # Fast path — reuse the cached client
    if _firestore_client is not None:
        return _firestore_client

    # Verify that base.py already called firebase_admin.initialize_app()
    try:
        firebase_admin.get_app()
    except ValueError:
        raise RuntimeError(
            "Firebase has not been initialized. "
            "Ensure Django settings (config/settings/base.py) are loaded "
            "before calling get_firestore_client()."
        )

    _firestore_client = firestore.client()
    logger.info("Firestore client created and cached for this process.")
    return _firestore_client


# ── Convenience helpers ───────────────────────────────────────────────────────

def org_collection(org_id: str, sub_collection: str):
    """
    Return a reference to  organisations/{org_id}/{sub_collection}.

    This is the standard way to scope any query to a single organisation.

    Parameters
    ----------
    org_id : str
        The organisation's primary key (as a string).
    sub_collection : str
        One of: 'resources', 'bookings', 'payments', etc.

    Example
    -------
        col = org_collection('42', 'resources')
        col.document('room-101').set({'name': 'Room 101'})
    """
    db = get_firestore_client()
    return db.collection('organisations').document(str(org_id)).collection(sub_collection)
