from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def extract_learning_path(pathway: Dict[str, Any]) -> Dict[str, Any]:
    lp = pathway.get("learning_path")
    if isinstance(lp, dict):
        return lp
    return pathway


@dataclass(frozen=True)
class UnitMeta:
    unit_id: str
    level: int
    level_title: str
    unit: int
    title: str
    skills: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "level": self.level,
            "level_title": self.level_title,
            "unit": self.unit,
            "title": self.title,
            "skills": list(self.skills),
        }


def build_unit_id(level_num: Any, unit_num: Any) -> str:
    try:
        level_int = int(level_num)
    except Exception:
        level_int = 0
    try:
        unit_int = int(unit_num)
    except Exception:
        unit_int = 0
    return f"L{level_int}U{unit_int}"


def flatten_units(learning_path: Dict[str, Any]) -> Tuple[List[str], Dict[str, UnitMeta]]:
    order: List[str] = []
    meta: Dict[str, UnitMeta] = {}

    for level in learning_path.get("levels", []) or []:
        level_num = level.get("level")
        level_title = str(level.get("title") or "").strip()
        for unit in level.get("units", []) or []:
            unit_num = unit.get("unit")
            unit_id = build_unit_id(level_num, unit_num)
            unit_title = str(unit.get("title") or "").strip()
            skills = unit.get("skills") or []
            if not isinstance(skills, list):
                skills = []
            skills = [str(s).strip() for s in skills if str(s).strip()]
            order.append(unit_id)
            meta[unit_id] = UnitMeta(
                unit_id=unit_id,
                level=int(level_num) if str(level_num).isdigit() else 0,
                level_title=level_title,
                unit=int(unit_num) if str(unit_num).isdigit() else 0,
                title=unit_title,
                skills=skills,
            )

    return order, meta


def init_progress(unit_order: List[str]) -> Dict[str, Dict[str, Any]]:
    progress = {unit_id: {"status": "locked"} for unit_id in unit_order}
    if unit_order:
        progress[unit_order[0]]["status"] = "unlocked"
    return progress


def next_unit_id(unit_order: List[str], current_unit_id: str) -> Optional[str]:
    try:
        idx = unit_order.index(current_unit_id)
    except ValueError:
        return None
    if idx + 1 >= len(unit_order):
        return None
    return unit_order[idx + 1]

