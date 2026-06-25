"""Candidate-safe LSTM retraining adapter status for MutantShield Evolution."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .contracts.validators import validate_lstm_buffer_contract
from .model_coverage import CANDIDATE_DIRS, discover_production_artifacts, empty_model_entry
from .reports import write_json


def train_lstm_candidate(
    out_dir: Path,
    cfg: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_cols: List[str],
    *,
    source_columns: Optional[List[str]] = None,
    supervised_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Return an honest LSTM training status.

    The production LSTM architecture exists, but the available production script is a
    monolithic trainer configured to write under models_final. Until it is converted
    into a reusable candidate-safe training API with verified metadata loading, the
    Evolution Engine must not count an LSTM surrogate as real retraining.
    """
    entry = empty_model_entry("LSTM")
    entry["candidate_training_attempted"] = True
    lstm_dir = out_dir / CANDIDATE_DIRS["LSTM"]
    lstm_dir.mkdir(parents=True, exist_ok=True)
    production = discover_production_artifacts(cfg)
    production_path = production.get("LSTM")
    training_script = (
        Path(__file__).resolve().parents[2]
        / "Mutant_Sheild Module"
        / "mutantshield"
        / "src"
        / "FinalVersion"
        / "LSTM_final  (Sequence)"
        / "LSTM_final.py"
    )
    blockers = []
    if not production_path:
        blockers.append("production_lstm_artifact_missing")
    if not training_script.exists():
        blockers.append("production_lstm_training_script_missing")
    contract_report = (
        validate_lstm_buffer_contract(supervised_df)
        if supervised_df is not None
        else {
            "valid": False,
            "missing_columns": ["sequence_id", "sequence_index", "timestamp", "flow_id"],
            "warnings": ["no_dataframe_available_for_contract_validation"],
            "safe_to_train": False,
            "contract_name": "lstm_retraining_contract",
            "contract_version": "1.0",
        }
    )
    if not contract_report.get("safe_to_train"):
        blockers.append("lstm_retraining_contract_not_satisfied")
    blockers.extend(
        [
            "production_lstm_trainer_is_monolithic_and_writes_models_final_by_default",
            "no_candidate_safe_lstm_training_api_available",
        ]
    )
    status = {
        "generated_at": time.time(),
        "status": "blocked_contract_missing" if not contract_report.get("safe_to_train") else "blocked",
        "blocker_reason": ";".join(blockers),
        "contract_validation": contract_report,
        "safe_to_train": bool(contract_report.get("safe_to_train")),
        "production_lstm_inference_available": bool(production_path),
        "production_lstm_artifact_path": production_path,
        "production_lstm_training_script": str(training_script) if training_script.exists() else None,
        "evolution_training_supported": False,
        "surrogate_used": False,
        "candidate_trained": False,
        "feature_count": len(feature_cols),
        "sample_count": int(len(X)),
        "note": "LSTM surrogate training is intentionally disabled; not counted as full retraining.",
    }
    path = lstm_dir / "lstm_training_report.json"
    write_json(path, status)
    write_json(lstm_dir / "lstm_candidate_status.json", status)
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
            "production_inference_available": bool(production_path),
            "safe_to_train": bool(contract_report.get("safe_to_train")),
            "contract_validation": contract_report,
        }
    )
    return entry
