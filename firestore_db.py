"""
Firestore database layer for user profiles and progress tracking.

Collections structure:
- users/{uid}
  - email, display_name, photo_url, created_at, last_login

- users/{uid}/progress/{topic}
  - coins, active_unit_id, updated_at
  - units: { "L1U1": "completed", "L1U2": "unlocked", ... }
"""

from google.cloud import firestore
from datetime import datetime
from typing import Optional, Dict, Any


# Global Firestore client
_db = None


def init_firestore(
    credentials_info: Optional[Dict[str, Any]] = None,
    credentials_path: Optional[str] = None,
) -> Optional[firestore.Client]:
    """Initialize Firestore client with optional service account credentials."""
    global _db
    if _db is not None:
        return _db

    if credentials_info:
        _db = firestore.Client.from_service_account_info(credentials_info)
    elif credentials_path:
        _db = firestore.Client.from_service_account_json(credentials_path)
    else:
        _db = firestore.Client()
    return _db


def get_firestore_client():
    """Get the initialized Firestore client."""
    if _db is None:
        init_firestore()
    return _db


def upsert_user(uid: str, email: str, display_name: str, photo_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Create or update a user document in Firestore.

    Args:
        uid: Firebase user ID
        email: User's email address
        display_name: User's display name from Google
        photo_url: Optional profile photo URL

    Returns:
        Dictionary with user data

    Firestore operation needed:
    - Reference: users/{uid}
    - On first creation: set created_at to current timestamp
    - Always update: email, display_name, photo_url, last_login to current timestamp
    - Use set() with merge=True to update without overwriting created_at
    """

    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)

    user_doc = user_ref.get()

    user_data = {
        'email': email,
        'display_name': display_name,
        'photo_url' : photo_url,
        'last_login': firestore.SERVER_TIMESTAMP
    }

    # new user
    if not user_doc.exists:
        user_data['created_at'] = firestore.SERVER_TIMESTAMP
    
    return {
        'uid': uid,
        'email': email,
        'display_name': display_name,
        'photo_url':photo_url
    }


    


def get_user(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from Firestore.

    Args:
        uid: Firebase user ID

    Returns:
        Dictionary with user data, or None if user doesn't exist

    Firestore operation needed:
    - Reference: users/{uid}
    - Use get() to fetch document
    - Return document data as dict, or None if not exists
    """
    
    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)

    user_doc = user_ref.get()
    if user_doc.exists:
        return user_doc.to_dict()
    return None



def save_progress(uid: str, topic: str, units: Dict[str, str], coins: int, active_unit_id: Optional[str] = None) -> None:
    """
    Save user progress for a specific topic to Firestore.

    Args:
        uid: Firebase user ID
        topic: Topic name (e.g., "Algebra")
        units: Dictionary of unit statuses {unit_id: status}
        coins: Current coin count
        active_unit_id: Currently active unit ID
    """
    db = get_firestore_client()
    progress_ref = db.collection('users').document(uid).collection('progress').document(topic)

    progress_ref.set({
        'units': units,
        'coins': coins,
        'active_unit_id': active_unit_id,
        'updated_at': firestore.SERVER_TIMESTAMP
    }, merge=True)


def get_progress(uid: str, topic: str) -> Optional[Dict[str, Any]]:
    """
    Get user progress for a specific topic from Firestore.

    Args:
        uid: Firebase user ID
        topic: Topic name

    Returns:
        Dictionary with progress data (units, coins, active_unit_id), or None if not found
    """
    db = get_firestore_client()
    progress_ref = db.collection('users').document(uid).collection('progress').document(topic)
    doc = progress_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None
