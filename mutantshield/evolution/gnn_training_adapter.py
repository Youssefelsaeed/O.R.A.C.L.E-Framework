"""Candidate-safe GNN retraining adapter status for MutantShield Evolution."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .contracts.validators import validate_gnn_buffer_contract
from .model_coverage import CANDIDATE_DIRS, discover_production_artifacts, empty_model_entry
from .reports import write_json

GRAPH_COLUMNS = {"src_ip", "dst_ip", "Source IP", "Destination IP", "Timestamp", "Flow ID"}


def train_gnn_candidate(
    out_dir: Path,
    cfg: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_cols: List[str],
    *,
    supervised_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Return an honest GNN training status.

    Production GNN inference artifacts exist, including a builder pickle, but real
    retraining requires graph edge/time context. Current adaptation buffers preserve
    mapped flow features and labels but not the host/time edge metadata needed to
    reconstruct training graphs safely.
    """
    entry = empty_model_entry("GNN")
    entry["candidate_training_attempted"] = True
    gnn_dir = out_dir / CANDIDATE_DIRS["GNN"]
    gnn_dir.mkdir(parents=True, exist_ok=True)
    production = discover_production_artifacts(cfg)
    production_path = production.get("GNN")
    root = Path(__file__).resolve().parents[2]
    builder_path = (
        root
        / "Mutant_Sheild Module"
        / "mutantshield"
        / "src"
        / "FinalVersion"
        / "models_final"
        / "GNN"
        / "gnn_graphsage_builder.pkl"
    )
    training_script = (
        root
        / "Mutant_Sheild Module"
        / "mutantshield"
        / "src"
        / "FinalVersion"
        / "GNN_final  (Graph)"
        / "GNN_final.py"
    )
    available_columns = set(str(c) for c in (supervised_df.columns if supervised_df is not None else []))
    graph_columns_present = sorted(available_columns.intersection(GRAPH_COLUMNS))
    blockers = []
    if not production_path:
        blockers.append("production_gnn_artifact_missing")
    if not builder_path.exists():
        blockers.append("production_gnn_builder_missing")
    if not training_script.exists():
        blockers.append("production_gnn_training_script_missing")
    if not graph_columns_present:
        blockers.append("adaptation_buffer_missing_src_dst_timestamp_graph_columns")
    contract_report = (
        validate_gnn_buffer_contract(supervised_df)
        if supervised_df is not None
        else {
            "valid": False,
            "missing_columns": ["flow_id", "src_ip", "dst_ip", "timestamp"],
            "warnings": ["no_dataframe_available_for_contract_validation"],
            "safe_to_train": False,
            "contract_name": "gnn_retraining_contract",
            "contract_version": "1.0",
        }
    )
    if not contract_report.get("safe_to_train"):
        blockers.append("gnn_retraining_contract_not_satisfied")
    blockers.extend(
        [
            "no_candidate_safe_gnn_training_api_available",
            "graph_reconstruction_from_current_buffers_not_safe",
        ]
    )
    status = {
        "generated_at": time.time(),
        "status": "blocked_contract_missing" if not contract_report.get("safe_to_train") else "blocked",
        "blocker_reason": ";".join(blockers),
        "contract_validation": contract_report,
        "safe_to_train": bool(contract_report.get("safe_to_train")),
        "production_gnn_inference_available": bool(production_path and builder_path.exists()),
        "production_gnn_artifact_path": production_path,
        "production_gnn_builder_path": str(builder_path) if builder_path.exists() else None,
        "production_gnn_training_script": str(training_script) if training_script.exists() else None,
        "evolution_training_supported": False,
        "surrogate_used": False,
        "candidate_trained": False,
        "feature_count": len(feature_cols),
        "sample_count": int(len(X)),
        "graph_columns_present": graph_columns_present,
        "required_graph_columns": sorted(GRAPH_COLUMNS),
        "note": "GNN retraining is blocked until graph edge/time metadata is available in candidate buffers.",
    }
    path = gnn_dir / "gnn_training_report.json"
    write_json(path, status)
    write_json(gnn_dir / "gnn_candidate_status.json", status)
    entry.update(
        {
            "candidate_trained": False,
            "retraining_supported": False,
            "promotion_eligible": False,
            "blocker_reason": status["blocker_reason"],
            "candidate_artifact_path": str(path),
            "status": status["status"],
            "real_retraining": False,
            "surrogate_used": False,
            "production_inference_available": bool(production_path and builder_path.exists()),
            "safe_to_train": bool(contract_report.get("safe_to_train")),
            "contract_validation": contract_report,
        }
    )
    return entry
