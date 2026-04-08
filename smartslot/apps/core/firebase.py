import logging
import firebase_admin
from firebase_admin import firestore

logger = logging.getLogger(__name__)

def get_firestore_client():
    """
    Returns a configured Firebase Firestore client instance.
    This assumes that `firebase_admin.initialize_app()` has already been
    successfully called in `config/settings/base.py`.
    """
    try:
        # Verify that the default Firebase app is initialized
        firebase_admin.get_app()
        return firestore.client()
    except ValueError as e:
        logger.error(f"Failed to get Firestore client. Firebase app not initialized: {e}")
        return None

# Export a single db instance for shared use across the application
db = get_firestore_client()
