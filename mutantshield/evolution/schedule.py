"""SOC-controlled MutantShield evolution schedule configuration."""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from mutantshield.evolution.config import EvolutionConfig, get_config

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_PATH = ROOT / "reports" / "evolution" / "evolution_schedule.json"

DEFAULT_SCHEDULE: Dict[str, Any] = {
    "enabled": False,
    "frequency": "weekly",
    "next_run": None,
    "last_run": None,
    "mode": "candidate-only",
    "use_art": True,
    "adversarial_train": True,
    "max_rows": 5000,
    "controlled_promotion_allowed": False,
    "require_human_approval": True,
    "status": "idle",
}


def load_schedule(path: Path = SCHEDULE_PATH) -> Dict[str, Any]:
    if path.exists():
        return {**DEFAULT_SCHEDULE, **json.loads(path.read_text(encoding="utf-8"))}
    return dict(DEFAULT_SCHEDULE)


def save_schedule(schedule: Dict[str, Any], path: Path = SCHEDULE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schedule, indent=2), encoding="utf-8")


def ensure_schedule_exists() -> Dict[str, Any]:
    sched = load_schedule()
    if not SCHEDULE_PATH.exists():
        save_schedule(sched)
    return sched


def _compute_next_run(frequency: str, from_ts: float | None = None) -> float:
    base = datetime.fromtimestamp(from_ts or time.time())
    if frequency == "daily":
        return (base + timedelta(days=1)).timestamp()
    if frequency == "weekly":
        return (base + timedelta(days=7)).timestamp()
    return base.timestamp()


def is_due(schedule: Dict[str, Any]) -> bool:
    if not schedule.get("enabled"):
        return False
    if schedule.get("frequency") == "manual":
        return False
    next_run = schedule.get("next_run")
    if next_run is None:
        return True
    return time.time() >= float(next_run)
