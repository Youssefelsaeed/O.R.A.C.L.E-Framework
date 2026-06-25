"""Candidate-only MutantShield inference helpers.

This module loads artifacts from models_candidate/<candidate_id>/ and never
touches production models_final.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from .config import get_config


RISK_THRESHOLDS = (
    (0.85, "CRITICAL"),
    (0.65, "HIGH"),
    (0.35, "MEDIUM"),
    (0.0, "LOW"),
)


class CandidateInferenceEngine:
    """Load and run a candidate model bundle in isolation."""

    def __init__(self, candidate_id: str) -> None:
        self.candidate_id = candidate_id
        self.cfg = get_config()
        self.candidate_dir = self.cfg.models_candidate_dir / candidate_id
        if not self.candidate_dir.exists():
            raise FileNotFoundError(f"candidate_dir_not_found:{self.candidate_dir}")

        self.metadata = self._load_metadata()
        self.decision_threshold = float(self.metadata.get("recommended_threshold", 0.5) or 0.5)
        self.feature_names = self._load_feature_schema()
        self.xgb = self._load_optional(self.candidate_dir / "XGboost" / "xgboost_candidate.pkl")
        self.ae_bundle = self._load_optional(self.candidate_dir / "AutoEncoder" / "autoencoder_candidate.pkl")
        self.fusion_bundle = self._load_optional(self.candidate_dir / "FusionEngine" / "fusion_candidate.pkl")

        if self.xgb is None:
            raise FileNotFoundError("candidate_xgboost_missing")

    def _load_feature_schema(self) -> List[str]:
        path = self.candidate_dir / "feature_schema.json"
        if not path.exists():
            raise FileNotFoundError(f"candidate_feature_schema_missing:{path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        features = [str(f).strip() for f in data.get("features", [])]
        if not features:
            raise ValueError("candidate_feature_schema_empty")
        return features

    def _load_metadata(self) -> Dict[str, Any]:
        path = self.candidate_dir / "candidate_metadata.json"
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @staticmethod
    def _load_optional(path: Path) -> Optional[Any]:
        if not path.exists():
            return None
        return joblib.load(path)

    def _vectorize(self, features: Dict[str, Any]) -> np.ndarray:
        arr = np.zeros((1, len(self.feature_names)), dtype=float)
        for i, name in enumerate(self.feature_names):
            try:
                value = float(features.get(name, 0.0))
            except Exception:
                value = 0.0
            if not np.isfinite(value):
                value = 0.0
            arr[0, i] = value
        return np.nan_to_num(arr, nan=0.0, posinf=1e6, neginf=-1e6)

    def _xgb_score(self, x: np.ndarray) -> float:
        if hasattr(self.xgb, "predict_proba"):
            proba = self.xgb.predict_proba(x)
            if getattr(proba, "shape", (0, 0))[1] > 1:
                return float(proba[0, 1])
        pred = self.xgb.predict(x)
        return float(pred[0])

    def _ae_error(self, x: np.ndarray) -> float:
        if not self.ae_bundle:
            return 0.0
        try:
            scaler = self.ae_bundle["scaler"]
            model = self.ae_bundle["model"]
            xs = scaler.transform(x)
            recon = model.predict(xs)
            return float(np.mean((xs - recon) ** 2))
        except Exception:
            return 0.0

    def _fusion_score(self, xgb_score: float, ae_error: float) -> Optional[float]:
        if not self.fusion_bundle:
            return None
        try:
            model = self.fusion_bundle["model"]
            fusion_x = np.asarray([[xgb_score, ae_error, 0.0, 0.0]], dtype=float)
            score = float(model.predict(fusion_x)[0])
            return max(0.0, min(1.0, score))
        except Exception:
            return None

    @staticmethod
    def _risk_label(score: float) -> str:
        for threshold, label in RISK_THRESHOLDS:
            if score >= threshold:
                return label
        return "LOW"

    @staticmethod
    def _confidence(score: float) -> str:
        distance = abs(score - 0.5)
        if distance >= 0.35:
            return "HIGH"
        if distance >= 0.2:
            return "MEDIUM"
        return "LOW"

    def predict(self, features: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
        x = self._vectorize(features)
        xgb_score = self._xgb_score(x)
        ae_error = self._ae_error(x)
        fusion_score = self._fusion_score(xgb_score, ae_error)
        score = fusion_score if fusion_score is not None else xgb_score
        score = max(0.0, min(1.0, float(score)))
        is_attack = score >= self.decision_threshold

        votes = []
        votes.append(xgb_score >= self.decision_threshold)
        if fusion_score is not None:
            votes.append(fusion_score >= self.decision_threshold)
        if self.ae_bundle is not None:
            # AutoEncoder contributes an anomaly vote only for substantial reconstruction error.
            votes.append(ae_error >= 1.0)
        positive = sum(1 for v in votes if v)

        decision = {
            "risk_score": score,
            "risk_label": self._risk_label(score),
            "is_attack": bool(is_attack),
            "attack_family": "cse_adapted_attack" if is_attack else "benign",
            "confidence_band": self._confidence(score),
            "model_consensus": f"{positive}/{len(votes)}",
        }
        raw = {
            "candidate_id": self.candidate_id,
            "candidate_dir": str(self.candidate_dir),
            "xgboost_score": round(xgb_score, 6),
            "autoencoder_error": round(ae_error, 6),
            "fusion_score": round(fusion_score, 6) if fusion_score is not None else None,
            "decision_source": "fusion" if fusion_score is not None else "xgboost",
            "decision_threshold": self.decision_threshold,
        }
        return decision, raw


def load_candidate(candidate_id: str) -> CandidateInferenceEngine:
    return CandidateInferenceEngine(candidate_id)
