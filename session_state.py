from typing import Any, Dict, Optional

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

def hydrate(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    state = default_state()
    if raw:
        state.update(raw)
    return state
