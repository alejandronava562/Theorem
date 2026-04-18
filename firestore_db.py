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

# Initialize Firestore client 
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

# Create or update user profile (stores basic info and last login)
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
    """

    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)

    user_doc = user_ref.get()

    user_data = {
        'email': email,
        'display_name': display_name,
        'photo_url': photo_url,
        'last_login': firestore.SERVER_TIMESTAMP
    }

    # new user
    if not user_doc.exists:
        user_data['created_at'] = firestore.SERVER_TIMESTAMP

    user_ref.set(user_data, merge=True)

    return {
        'uid': uid,
        'email': email,
        'display_name': display_name,
        'photo_url': photo_url
    }


    

# Fetch user profile by UID 
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


# Save user progress for a topic (units status, coins, active unit)
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

# Load saved progress for a topic
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

# Save generated learning path and unit metadata for a topic
def save_learning_path(uid: str, topic: str, learning_path: Dict[str, Any], unit_meta: Dict[str, Any], unit_order: list) -> None:
    """
    Save the AI-generated learning path outline for a topic.

    Args:
        uid: Firebase user ID
        topic: Topic name
        learning_path: The complete learning path structure from AI
        unit_meta: Unit metadata (titles, skills, etc.)
        unit_order: Order of unit IDs
    """
    db = get_firestore_client()
    path_ref = db.collection('users').document(uid).collection('learning_paths').document(topic)

    path_ref.set({
        'learning_path': learning_path,
        'unit_meta': unit_meta,
        'unit_order': unit_order,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP
    }, merge=True)

# Load saved learning path for a topic
def get_learning_path(uid: str, topic: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve saved learning path for a topic.

    Args:
        uid: Firebase user ID
        topic: Topic name

    Returns:
        Dictionary with learning_path, unit_meta, unit_order, or None if not found
    """
    db = get_firestore_client()
    path_ref = db.collection('users').document(uid).collection('learning_paths').document(topic)
    doc = path_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None

# Save full session state 
def save_session_state(uid: str, topic: str, session_data: Dict[str, Any]) -> None:
    """
    Save complete session state for a topic (progress, coins, active unit, lessons, etc.).

    Args:
        uid: Firebase user ID
        topic: Topic name
        session_data: Complete session state dictionary
    """
    db = get_firestore_client()
    session_ref = db.collection('users').document(uid).collection('sessions').document(topic)

    session_ref.set({
        'progress': session_data.get('progress', {}),
        'coins': session_data.get('coins', 0),
        'active_unit_id': session_data.get('active_unit_id'),
        'lessons': session_data.get('lessons', []),
        'questions': session_data.get('questions', []),
        'q_index': session_data.get('q_index', 0),
        'updated_at': firestore.SERVER_TIMESTAMP
    }, merge=True)

# Load saved session state for a topic
def get_session_state(uid: str, topic: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve saved session state for a topic.

    Args:
        uid: Firebase user ID
        topic: Topic name

    Returns:
        Dictionary with session data, or None if not found
    """
    db = get_firestore_client()
    session_ref = db.collection('users').document(uid).collection('sessions').document(topic)
    doc = session_ref.get()

    if doc.exists:
        return doc.to_dict()
    return None

# Delete all user-related data across subcollections
def delete_user_data(uid: str) -> Dict[str, int]:
    """
    Delete all saved data for a user (learning paths, progress, sessions).

    Args:
        uid: Firebase user ID

    Returns:
        Dictionary with counts of deleted documents per subcollection
    """
    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)
    deleted = {}

    for subcol_name in ('learning_paths', 'progress', 'sessions'):
        count = 0
        docs = user_ref.collection(subcol_name).stream()
        for doc in docs:
            doc.reference.delete()
            count += 1
        deleted[subcol_name] = count

    return deleted

# List all topics the user has started
def get_all_topics_for_user(uid: str) -> list:
    """
    Get list of all topics the user has started.

    Args:
        uid: Firebase user ID

    Returns:
        List of topic names
    """
    db = get_firestore_client()
    learning_paths = db.collection('users').document(uid).collection('learning_paths').stream()
    return [doc.id for doc in learning_paths]
