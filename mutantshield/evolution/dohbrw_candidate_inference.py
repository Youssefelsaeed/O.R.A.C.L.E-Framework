"""Candidate-only inference for native DoHBrw anomaly adapters."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from .config import get_config
from .dohbrw_native_adapter import native_features_from_row


class DoHBrwCandidateInference:
    def __init__(self, candidate_id: str) -> None:
        self.candidate_id = candidate_id
        cfg = get_config()
        self.candidate_dir = cfg.models_candidate_dir / candidate_id
        self.adapter_dir = self.candidate_dir / "DoHBrwAdapter"
        if not self.adapter_dir.exists():
            raise FileNotFoundError(f"dohbrw_adapter_missing:{self.adapter_dir}")
        self.metadata = self._read_json(self.adapter_dir / "dohbrw_adapter_metadata.json")
        schema = self._read_json(self.adapter_dir / "native_feature_schema.json")
        self.feature_names: List[str] = [str(f) for f in schema.get("features", [])]
        if not self.feature_names:
            raise RuntimeError("native_feature_schema_empty")
        self.scaler = joblib.load(self.adapter_dir / "scaler.pkl")
        self.isolation_forest = joblib.load(self.adapter_dir / "isolation_forest.pkl")
        self.oneclass_svm = self._load_optional("oneclass_svm.pkl")
        self.autoencoder = self._load_optional("autoencoder.pkl")
        self.xgboost = self._load_optional("dohbrw_xgboost.pkl")
        self.threshold = float(self.metadata.get("recommended_threshold", 0.5) or 0.5)
        self.calibration = self.metadata.get("calibration") or {}

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def _load_optional(self, name: str) -> Optional[Any]:
        path = self.adapter_dir / name
        return joblib.load(path) if path.exists() else None

    def _vectorize(self, row: Any) -> Tuple[np.ndarray, Dict[str, Any]]:
        series = row if isinstance(row, pd.Series) else pd.Series(row)
        features, quality = native_features_from_row(series, self.feature_names)
        arr = np.asarray([[features[f] for f in self.feature_names]], dtype=float)
        return np.nan_to_num(arr, nan=0.0, posinf=1e9, neginf=-1e9), quality

    @staticmethod
    def _norm(raw: np.ndarray, bounds: List[float]) -> np.ndarray:
        lo, hi = float(bounds[0]), float(bounds[1])
        return np.clip((raw - lo) / max(1e-9, hi - lo), 0.0, 1.0)

    def _component_scores(self, x_scaled: np.ndarray) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        raw_if = -self.isolation_forest.decision_function(x_scaled)
        scores["isolation_forest"] = float(self._norm(raw_if, self.calibration.get("isolation_forest_range", [0.0, 1.0]))[0])
        if self.oneclass_svm is not None:
            raw_svm = -self.oneclass_svm.decision_function(x_scaled)
            scores["oneclass_svm"] = float(self._norm(raw_svm, self.calibration.get("oneclass_svm_range", [0.0, 1.0]))[0])
        if self.autoencoder is not None:
            recon = self.autoencoder.predict(x_scaled)
            raw_ae = np.mean((x_scaled - recon) ** 2, axis=1)
            scores["autoencoder"] = float(self._norm(raw_ae, self.calibration.get("autoencoder_range", [0.0, 1.0]))[0])
        if self.xgboost is not None:
            if hasattr(self.xgboost, "predict_proba"):
                scores["xgboost"] = float(self.xgboost.predict_proba(x_scaled)[0, 1])
            else:
                scores["xgboost"] = float(self.xgboost.predict(x_scaled)[0])
        return scores

    @staticmethod
    def _risk_label(score: float) -> str:
        if score >= 0.85:
            return "CRITICAL"
        if score >= 0.65:
            return "HIGH"
        if score >= 0.35:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _confidence(score: float) -> str:
        dist = abs(score - 0.5)
        if dist >= 0.35:
            return "HIGH"
        if dist >= 0.2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _combine(scores: Dict[str, float]) -> float:
        weights = {
            "xgboost": 0.45,
            "isolation_forest": 0.25,
            "autoencoder": 0.20,
            "oneclass_svm": 0.10,
        }
        total = sum(weights[k] for k in scores if k in weights) or 1.0
        combined = sum((weights.get(k, 0.0) / total) * v for k, v in scores.items())
        return max(0.0, min(1.0, float(combined)))

    def predict(self, row: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        x, quality = self._vectorize(row)
        x_scaled = self.scaler.transform(x)
        scores = self._component_scores(x_scaled)
        risk_score = self._combine(scores)
        votes = sum(1 for value in scores.values() if value >= self.threshold)
        total = len(scores)
        is_attack = risk_score >= self.threshold
        decision = {
            "risk_score": risk_score,
            "risk_label": self._risk_label(risk_score),
            "is_attack": bool(is_attack),
            "attack_family": "dohbrw_anomaly" if is_attack else "benign",
            "confidence_band": self._confidence(risk_score),
            "model_consensus": f"{votes}/{total}",
            "adapter_name": "DoHBrwAdapter",
        }
        raw = {
            "candidate_id": self.candidate_id,
            "adapter_dir": str(self.adapter_dir),
            "threshold": self.threshold,
            "component_scores": scores,
            "feature_quality": quality,
        }
        return decision, raw


def load_dohbrw_candidate(candidate_id: str) -> DoHBrwCandidateInference:
    return DoHBrwCandidateInference(candidate_id)
