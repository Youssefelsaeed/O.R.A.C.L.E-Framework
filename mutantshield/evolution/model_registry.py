"""Model version registry."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .config import EvolutionConfig
from .reports import read_json, write_json


def list_versions(cfg: EvolutionConfig) -> List[Dict[str, Any]]:
    data = read_json(cfg.model_versions_path)
    return data.get("versions", [])


def register_version(cfg: EvolutionConfig, entry: Dict[str, Any]) -> Dict[str, Any]:
    data = read_json(cfg.model_versions_path)
    versions: List[Dict[str, Any]] = data.get("versions", [])
    versions.append(entry)
    write_json(cfg.model_versions_path, {"versions": versions, "updated_at": time.time()})
    return entry


def get_latest_promoted(cfg: EvolutionConfig) -> Optional[Dict[str, Any]]:
    versions = list_versions(cfg)
    promoted = [v for v in versions if v.get("promoted")]
    return promoted[-1] if promoted else None
