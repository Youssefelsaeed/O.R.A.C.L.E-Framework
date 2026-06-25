"""Train candidate XGBoost / AutoEncoder without touching production models."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from .config import EvolutionConfig
from .reports import read_json, write_json
from .schema_validation import validate_feature_schema

DEPENDENCIES: Dict[str, bool] = {}


def _check_deps() -> Dict[str, bool]:
    global DEPENDENCIES
    if DEPENDENCIES:
        return DEPENDENCIES
    try:
        import xgboost  # noqa: F401

        DEPENDENCIES["xgboost"] = True
    except ImportError:
        DEPENDENCIES["xgboost"] = False
    try:
        import sklearn  # noqa: F401

        DEPENDENCIES["sklearn"] = True
    except ImportError:
        DEPENDENCIES["sklearn"] = False
    return DEPENDENCIES


def _prepare_xy(
    df: pd.DataFrame,
    production_schema: Optional[List[str]] = None,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    exclude = {"label", "is_attack", "label_trust", "source", "flow_id", "oracle_trace_id", "evidence_bucket"}
    if production_schema:
        feature_cols = [str(f).strip() for f in production_schema]
        X = np.zeros((len(df), len(feature_cols)), dtype=float)
        for i, col in enumerate(feature_cols):
            if col in df.columns:
                X[:, i] = df[col].fillna(0).astype(float).values
    else:
        feature_cols = [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
        if not feature_cols:
            feature_cols = [c for c in df.columns if c not in exclude]
        X = df[feature_cols].fillna(0).astype(float).values
    X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
    if "is_attack" in df.columns:
        y = df["is_attack"].astype(int).values
    else:
        y = np.zeros(len(df), dtype=int)
    return X, y, feature_cols


def _load_production_feature_schema(cfg: EvolutionConfig) -> Optional[List[str]]:
    baseline_path = cfg.reports_dir / "production_baseline_metrics.json"
    if baseline_path.exists():
        data = read_json(baseline_path)
        schema = data.get("feature_schema")
        if schema:
            return [str(f).strip() for f in schema]

    schema_paths = [
        cfg.models_final_dir / "XGboost" / "feature_schema.json",
        cfg.models_final_dir / "feature_schema.json",
    ]
    for p in schema_paths:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [str(f).strip() for f in data]
            if isinstance(data, dict) and "features" in data:
                return [str(f).strip() for f in data["features"]]

    try:
        import joblib

        xgb_path = cfg.models_final_dir / "XGboost" / "xgboost_classifier.pkl"
        if not xgb_path.exists():
            for candidate in cfg.models_final_dir.rglob("xgboost_classifier.pkl"):
                xgb_path = candidate
                break
        if xgb_path.exists():
            bundle = joblib.load(xgb_path)
            names = bundle.get("feature_names", [])
            if names:
                return [str(f).strip() for f in names]
    except Exception:
        pass
    return None


def train_candidates(
    cfg: EvolutionConfig,
    supervised_df: pd.DataFrame,
    training_sources: List[str],
) -> Dict[str, Any]:
    deps = _check_deps()
    candidate_id = f"candidate-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    out_dir = cfg.models_candidate_dir / candidate_id
    out_dir.mkdir(parents=True, exist_ok=True)

    if supervised_df.empty or len(supervised_df) < max(10, cfg.min_samples // 10):
        # Use sklearn fallback with minimal synthetic if buffer too small for full min_samples
        if supervised_df.empty:
            return {
                "success": False,
                "candidate_id": candidate_id,
                "candidate_dir": str(out_dir),
                "error": "empty_supervised_buffer",
            }

    prod_schema = _load_production_feature_schema(cfg)
    X, y, feature_cols = _prepare_xy(supervised_df, production_schema=prod_schema)
    schema_compatible = True
    schema_report: Dict[str, Any] = {"status": "no_production_schema"}
    if prod_schema:
        schema_report = validate_feature_schema(feature_cols, prod_schema)
        schema_compatible = bool(schema_report.get("compatible", False))

    label_dist = {
        "attack": int((y == 1).sum()),
        "benign": int((y == 0).sum()),
    }
    artifacts: Dict[str, str] = {}
    dependency_missing: List[str] = []
    models_trained: List[str] = []

    # XGBoost candidate
    if "xgboost" in cfg.target_models:
        if deps.get("xgboost") and deps.get("sklearn"):
            from sklearn.model_selection import train_test_split
            from xgboost import XGBClassifier

            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None)
            model = XGBClassifier(
                n_estimators=50,
                max_depth=4,
                learning_rate=0.1,
                eval_metric="logloss",
                random_state=42,
            )
            model.fit(X_tr, y_tr)
            xgb_path = out_dir / "xgboost_candidate.pkl"
            joblib.dump(model, xgb_path)
            artifacts["xgboost"] = str(xgb_path)
            models_trained.append("xgboost")
        elif deps.get("sklearn"):
            from sklearn.ensemble import RandomForestClassifier

            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(X, y)
            xgb_path = out_dir / "xgboost_candidate.pkl"
            joblib.dump(model, xgb_path)
            artifacts["xgboost"] = str(xgb_path)
            models_trained.append("xgboost_fallback_rf")
            dependency_missing.append("xgboost")
        else:
            dependency_missing.append("xgboost")
            dependency_missing.append("sklearn")

    # AutoEncoder candidate (sklearn MLP fallback)
    if "autoencoder" in cfg.target_models:
        if deps.get("sklearn"):
            from sklearn.neural_network import MLPRegressor
            from sklearn.preprocessing import StandardScaler

            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)
            ae = MLPRegressor(hidden_layer_sizes=(min(32, X.shape[1]), min(16, X.shape[1])), max_iter=100, random_state=42)
            ae.fit(Xs, Xs)
            ae_path = out_dir / "autoencoder_candidate.pkl"
            joblib.dump({"model": ae, "scaler": scaler}, ae_path)
            artifacts["autoencoder"] = str(ae_path)
            models_trained.append("autoencoder")
        else:
            dependency_missing.append("sklearn")

    schema_path = out_dir / "feature_schema.json"
    schema_path.write_text(json.dumps({"features": feature_cols}, indent=2), encoding="utf-8")

    metadata = {
        "candidate_id": candidate_id,
        "created_at": time.time(),
        "training_sources": training_sources,
        "sample_count": len(supervised_df),
        "feature_count": len(feature_cols),
        "label_distribution": label_dist,
        "training_mode": "candidate_v1",
        "dependencies_used": deps,
        "dependency_missing": dependency_missing,
        "models_trained": models_trained,
        "schema_compatible": schema_compatible,
        "schema_validation": schema_report,
        "production_feature_schema": prod_schema or [],
        "artifacts": artifacts,
    }
    write_json(out_dir / "candidate_metadata.json", metadata)
    sources: List[str] = []
    if "source" in supervised_df.columns:
        sources = [_normalize_training_source(s) for s in supervised_df["source"].tolist()]
    return {
        "success": len(models_trained) > 0,
        "candidate_id": candidate_id,
        "candidate_dir": str(out_dir),
        "metadata": metadata,
        "X": X,
        "y": y,
        "feature_cols": feature_cols,
        "sources": sources,
    }


def _normalize_training_source(raw: Any) -> str:
    s = str(raw).strip()
    if s == "art":
        return "art_adversarial"
    return s
