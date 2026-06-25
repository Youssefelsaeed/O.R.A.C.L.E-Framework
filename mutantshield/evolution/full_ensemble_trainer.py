"""Full MutantShield ensemble candidate training — never touches models_final."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from .candidate_trainer import _check_deps, _load_production_feature_schema, _prepare_xy
from .config import EvolutionConfig
from .gnn_training_adapter import train_gnn_candidate
from .lstm_training_adapter import train_lstm_candidate
from .model_coverage import (
    CANDIDATE_DIRS,
    ENSEMBLE_MODELS,
    build_coverage_report,
    discover_production_artifacts,
    empty_model_entry,
)
from .reports import write_json
from .schema_validation import validate_feature_schema


def _write_status(out_dir: Path, filename: str, payload: Dict[str, Any]) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    write_json(path, payload)
    return str(path)


def _train_xgboost(out_dir: Path, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    entry = empty_model_entry("XGBoost")
    entry["candidate_training_attempted"] = True
    xgb_dir = out_dir / CANDIDATE_DIRS["XGBoost"]
    xgb_dir.mkdir(parents=True, exist_ok=True)
    deps = _check_deps()
    try:
        if deps.get("xgboost") and deps.get("sklearn"):
            from sklearn.model_selection import train_test_split
            from xgboost import XGBClassifier

            X_tr, _, y_tr, _ = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
            )
            model = XGBClassifier(n_estimators=50, max_depth=4, learning_rate=0.1, random_state=42)
            model.fit(X_tr, y_tr)
            path = xgb_dir / "xgboost_candidate.pkl"
            joblib.dump(model, path)
            entry.update(
                {
                    "candidate_trained": True,
                    "promotion_eligible": True,
                    "candidate_artifact_path": str(path),
                    "status": "trained",
                }
            )
        else:
            entry.update(
                {
                    "retraining_supported": False,
                    "blocker_reason": "missing_xgboost_or_sklearn",
                    "status": "blocked",
                }
            )
    except Exception as exc:
        entry.update({"blocker_reason": str(exc), "status": "error"})
    return entry


def _train_autoencoder(out_dir: Path, X: np.ndarray) -> Dict[str, Any]:
    entry = empty_model_entry("AutoEncoder")
    entry["candidate_training_attempted"] = True
    ae_dir = out_dir / CANDIDATE_DIRS["AutoEncoder"]
    ae_dir.mkdir(parents=True, exist_ok=True)
    deps = _check_deps()
    try:
        if deps.get("sklearn"):
            from sklearn.neural_network import MLPRegressor
            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)
            ae = MLPRegressor(
                hidden_layer_sizes=(min(32, X.shape[1]), min(16, X.shape[1])),
                max_iter=100,
                random_state=42,
            )
            ae.fit(Xs, Xs)
            path = ae_dir / "autoencoder_candidate.pkl"
            joblib.dump({"model": ae, "scaler": scaler}, path)
            entry.update(
                {
                    "candidate_trained": True,
                    "promotion_eligible": True,
                    "candidate_artifact_path": str(path),
                    "status": "trained",
                }
            )
        else:
            entry.update(
                {
                    "retraining_supported": False,
                    "blocker_reason": "missing_sklearn",
                    "status": "blocked",
                }
            )
    except Exception as exc:
        entry.update({"blocker_reason": str(exc), "status": "error"})
    return entry


def _attempt_lstm(out_dir: Path, cfg: EvolutionConfig, X: np.ndarray, y: np.ndarray, feature_cols: List[str], supervised_df: pd.DataFrame) -> Dict[str, Any]:
    return train_lstm_candidate(out_dir, cfg, X, y, feature_cols, supervised_df=supervised_df)


def _attempt_gnn(out_dir: Path, cfg: EvolutionConfig, X: np.ndarray, y: np.ndarray, feature_cols: List[str], supervised_df: pd.DataFrame) -> Dict[str, Any]:
    return train_gnn_candidate(out_dir, cfg, X, y, feature_cols, supervised_df=supervised_df)


def _attempt_fusion(out_dir: Path, xgb_entry: Dict[str, Any], ae_entry: Dict[str, Any], X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    entry = empty_model_entry("FusionMLP")
    entry["candidate_training_attempted"] = True
    fusion_dir = out_dir / CANDIDATE_DIRS["FusionMLP"]
    fusion_dir.mkdir(parents=True, exist_ok=True)
    if not xgb_entry.get("candidate_trained") or not ae_entry.get("candidate_trained"):
        status = {
            "retraining_supported": False,
            "reason": "requires_base_model_candidate_outputs",
            "xgb_ready": xgb_entry.get("candidate_trained", False),
            "autoencoder_ready": ae_entry.get("candidate_trained", False),
        }
        path = _write_status(fusion_dir, "fusion_candidate_status.json", status)
        entry.update(
            {
                "retraining_supported": False,
                "blocker_reason": "requires_base_model_candidate_outputs",
                "candidate_artifact_path": path,
                "status": "blocked",
            }
        )
        return entry

    try:
        xgb = joblib.load(xgb_entry["candidate_artifact_path"])
        ae_bundle = joblib.load(ae_entry["candidate_artifact_path"])
        ae = ae_bundle["model"]
        scaler = ae_bundle["scaler"]
        xgb_scores = xgb.predict_proba(X)[:, 1] if hasattr(xgb, "predict_proba") else xgb.predict(X).astype(float)
        Xs = scaler.transform(X)
        recon = ae.predict(Xs)
        ae_err = np.mean((Xs - recon) ** 2, axis=1)
        fusion_X = np.column_stack([xgb_scores, ae_err, np.zeros(len(X)), np.zeros(len(X))])
        from sklearn.neural_network import MLPRegressor

        target = y.astype(float)
        fusion = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=100, random_state=42)
        fusion.fit(fusion_X, target)
        path = fusion_dir / "fusion_candidate.pkl"
        joblib.dump({"model": fusion, "input_dim": 4}, path)
        entry.update(
            {
                "candidate_trained": True,
                "promotion_eligible": False,
                "blocker_reason": "fusion_surrogate_requires_full_ensemble_validation",
                "candidate_artifact_path": str(path),
                "status": "surrogate_trained",
            }
        )
    except Exception as exc:
        status = {"retraining_supported": False, "reason": "requires_base_model_candidate_outputs", "error": str(exc)}
        path = _write_status(fusion_dir, "fusion_candidate_status.json", status)
        entry.update(
            {
                "retraining_supported": False,
                "blocker_reason": "requires_base_model_candidate_outputs",
                "candidate_artifact_path": path,
                "status": "error",
            }
        )
    return entry


def _gan_status(out_dir: Path) -> Dict[str, Any]:
    entry = empty_model_entry("GAN")
    entry["candidate_training_attempted"] = False
    gan_dir = out_dir / CANDIDATE_DIRS["GAN"]
    status = {
        "gan_status": "not_trained",
        "training_required": True,
        "recommendation": "train_gan_in_dedicated_phase",
    }
    path = _write_status(gan_dir, "gan_candidate_status.json", status)
    entry.update(
        {
            "retraining_supported": False,
            "blocker_reason": "gan_not_trained",
            "candidate_artifact_path": path,
            "status": "not_trained",
        }
    )
    return entry


def train_full_ensemble(
    cfg: EvolutionConfig,
    supervised_df: pd.DataFrame,
    training_sources: List[str],
    *,
    candidate_id: Optional[str] = None,
) -> Dict[str, Any]:
    if supervised_df.empty:
        cid = candidate_id or f"candidate-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        out_dir = cfg.models_candidate_dir / cid
        out_dir.mkdir(parents=True, exist_ok=True)
        return {
            "success": False,
            "candidate_id": cid,
            "candidate_dir": str(out_dir),
            "error": "empty_supervised_buffer",
            "model_results": [],
        }

    cid = candidate_id or f"candidate-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    out_dir = cfg.models_candidate_dir / cid
    out_dir.mkdir(parents=True, exist_ok=True)

    prod_schema = _load_production_feature_schema(cfg)
    X, y, feature_cols = _prepare_xy(supervised_df, production_schema=prod_schema)
    schema_report = validate_feature_schema(feature_cols, prod_schema) if prod_schema else {"status": "no_production_schema"}
    schema_compatible = bool(schema_report.get("compatible", True)) if prod_schema else True

    xgb_r = _train_xgboost(out_dir, X, y)
    ae_r = _train_autoencoder(out_dir, X)
    results = [
        xgb_r,
        ae_r,
        _attempt_lstm(out_dir, cfg, X, y, feature_cols, supervised_df),
        _attempt_gnn(out_dir, cfg, X, y, feature_cols, supervised_df),
        _attempt_fusion(out_dir, xgb_r, ae_r, X, y),
        _gan_status(out_dir),
    ]

    artifacts: Dict[str, str] = {}
    if xgb_r.get("candidate_artifact_path"):
        artifacts["xgboost"] = xgb_r["candidate_artifact_path"]
    if ae_r.get("candidate_artifact_path"):
        artifacts["autoencoder"] = ae_r["candidate_artifact_path"]

    schema_path = out_dir / "feature_schema.json"
    schema_path.write_text(json.dumps({"features": feature_cols}, indent=2), encoding="utf-8")

    metadata = {
        "candidate_id": cid,
        "created_at": time.time(),
        "training_sources": training_sources,
        "sample_count": len(supervised_df),
        "feature_count": len(feature_cols),
        "training_mode": "full_ensemble_v1",
        "schema_compatible": schema_compatible,
        "schema_validation": schema_report,
        "production_feature_schema": prod_schema or [],
        "artifacts": artifacts,
        "models_trained": [m["model_name"] for m in results if m.get("candidate_trained")],
    }
    write_json(out_dir / "candidate_metadata.json", metadata)
    coverage = build_coverage_report(cfg, results, candidate_dir=out_dir)

    sources: List[str] = []
    if "source" in supervised_df.columns:
        sources = [str(s).strip() for s in supervised_df["source"].tolist()]

    return {
        "success": xgb_r.get("candidate_trained", False) and ae_r.get("candidate_trained", False),
        "candidate_id": cid,
        "candidate_dir": str(out_dir),
        "metadata": metadata,
        "model_results": results,
        "coverage_report": coverage,
        "X": X,
        "y": y,
        "feature_cols": feature_cols,
        "sources": sources,
    }
