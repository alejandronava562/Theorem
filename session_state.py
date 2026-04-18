from typing import Any, Dict, Optional
# Defines default session state structure and helper to restore state
# Returns initial session state with default values
def default_state() -> Dict[str, Any]:
    return {
        "user": None,
        "topic": None,
        "use_tutor": False,
        "learning_path": None,
        "coins": 0,
        "progress": {},
        "unit_order": [],
        "unit_meta": {},
        "active_unit_id": None,
        "lessons": [],
        "questions": [],
        "q_index" : 0,
    }
# Merges saved state with defaults to ensure all fields exist
def hydrate(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    state = default_state()
    if raw:
        state.update(raw)
    return state
