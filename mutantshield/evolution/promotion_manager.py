"""Promotion and rollback — never overwrite production in dry-run."""
from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .config import EvolutionConfig
from .model_registry import get_latest_promoted, list_versions, register_version
from .reports import read_json, write_json


def archive_current_models(cfg: EvolutionConfig) -> Optional[str]:
    src = cfg.models_final_dir
    if not src.exists():
        return None
    archive_dir = cfg.models_archive_dir / time.strftime("%Y%m%d-%H%M%S")
    archive_dir.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        dest = archive_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    return str(archive_dir)


def promote_candidate(
    cfg: EvolutionConfig,
    candidate_dir: Path,
    evaluation_report: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "promoted": False,
        "simulated": cfg.dry_run,
        "rollback_available": False,
        "message": "",
    }

    if not evaluation_report.get("promotion_allowed"):
        result["message"] = "promotion_blocked_by_evaluation_gate"
        return result

    if cfg.dry_run:
        result["message"] = "dry_run_simulated_promotion"
        result["simulated"] = True
        register_version(
            cfg,
            {
                "model_version": metadata.get("candidate_id"),
                "created_at": time.time(),
                "model_paths": metadata.get("artifacts", {}),
                "feature_schema_path": str(candidate_dir / "feature_schema.json"),
                "metrics": evaluation_report.get("candidate_metrics", {}),
                "promoted": False,
                "simulated": True,
                "archived_from": None,
                "rollback_available": True,
            },
        )
        return result

    if not cfg.auto_promote and not cfg.force_promote:
        result["message"] = "auto_promote_disabled"
        return result

    archived = archive_current_models(cfg)
    result["rollback_available"] = archived is not None
    result["archived_from"] = archived

    # Copy candidate artifacts into production tree (XGBoost / AutoEncoder only)
    prod = cfg.models_final_dir
    prod.mkdir(parents=True, exist_ok=True)
    xgb_src = candidate_dir / "xgboost_candidate.pkl"
    ae_src = candidate_dir / "autoencoder_candidate.pkl"
    if xgb_src.exists():
        xgb_dest = prod / "XGboost"
        xgb_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(xgb_src, xgb_dest / "xgboost_classifier_candidate_promoted.pkl")
    if ae_src.exists():
        ae_dest = prod / "AutoEncoder"
        ae_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ae_src, ae_dest / "autoencoder_candidate_promoted.pkl")

    register_version(
        cfg,
        {
            "model_version": metadata.get("candidate_id"),
            "created_at": time.time(),
            "model_paths": metadata.get("artifacts", {}),
            "feature_schema_path": str(candidate_dir / "feature_schema.json"),
            "metrics": evaluation_report.get("candidate_metrics", {}),
            "promoted": True,
            "archived_from": archived,
            "rollback_available": True,
        },
    )
    result["promoted"] = True
    result["message"] = "promoted_to_candidate_promoted_files"
    return result


def rollback_to_previous(cfg: EvolutionConfig) -> Dict[str, Any]:
    versions = list_versions(cfg)
    archived = [v for v in versions if v.get("archived_from")]
    if not archived:
        return {"success": False, "message": "no_archive_available"}
    last = archived[-1]
    archive_path = Path(last["archived_from"])
    if not archive_path.exists():
        return {"success": False, "message": "archive_path_missing"}
    if cfg.dry_run:
        return {"success": True, "simulated": True, "message": "dry_run_rollback_simulated"}
    prod = cfg.models_final_dir
    for item in archive_path.iterdir():
        dest = prod / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    return {"success": True, "message": "rollback_completed", "restored_from": str(archive_path)}
