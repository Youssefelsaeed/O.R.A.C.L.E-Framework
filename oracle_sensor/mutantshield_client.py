from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


logger = logging.getLogger("oracle_sensor.mutantshield")

_FUSION_ENGINE: Any = None
_LOAD_ERROR: Optional[str] = None


def _init_fusion_engine() -> None:
    """Load real MutantShield FusionEngineV2 and all model bundles."""
    global _FUSION_ENGINE, _LOAD_ERROR
    if _FUSION_ENGINE is not None or _LOAD_ERROR is not None:
        return

    try:
        workspace = Path(__file__).resolve().parent.parent
        final_dir = (
            workspace
            / "Mutant_Sheild Module"
            / "mutantshield"
            / "src"
            / "FinalVersion"
        )

        fusion_dir = final_dir / "Fusion engine_V2"
        if not fusion_dir.exists():
            raise FileNotFoundError(f"Fusion directory missing: {fusion_dir}")

        # Ensure MutantShield modules are importable.
        for p in [str(fusion_dir), str(final_dir)]:
            if p not in sys.path:
                sys.path.insert(0, p)

        from FusionEngine_final import FusionEngineV2  # type: ignore
        from run_mutantshield_trial import MODEL_PATHS  # type: ignore

        # Validate required model files.
        required = [
            "xgboost",
            "autoencoder",
            "lstm",
            "gnn_model",
            "gnn_builder",
        ]
        missing = [k for k in required if not Path(MODEL_PATHS.get(k, "")).exists()]
        if missing:
            raise FileNotFoundError(f"Missing MutantShield model files: {missing}")

        _FUSION_ENGINE = FusionEngineV2(
            model_paths=MODEL_PATHS,
            detector_profile="high_recall",
            device="cpu",
        )
        logger.info({"msg": "mutantshield_fusion_loaded", "model_keys": required})
    except Exception as exc:
        _LOAD_ERROR = str(exc)
        logger.error({"msg": "mutantshield_fusion_load_failed", "error": _LOAD_ERROR})


def _heuristic_decision(features: Dict[str, float]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Safety fallback used ONLY when real model loading fails.
    """
    length = float(features.get("length", 0.0))
    risk = min(1.0, length / 1500.0) if length > 0 else 0.1
    if risk > 0.7:
        label = "HIGH"
    elif risk > 0.4:
        label = "MEDIUM"
    else:
        label = "LOW"
    decision = {
        "risk_score": float(risk),
        "risk_label": label,
        "is_attack": bool(risk > 0.6),
        "confidence_band": "LOW",
        "model_consensus": "fallback",
        "attack_family": "unknown",
    }
    raw = {"source": "fallback_heuristic", "load_error": _LOAD_ERROR}
    return decision, raw


def predict_decision(features: Dict[str, float]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Run MutantShield FusionEngine and return:
      (decision_object, raw_result)

    decision_object keys:
      risk_score, risk_label, is_attack, confidence_band, model_consensus, attack_family
    """
    _init_fusion_engine()
    if _FUSION_ENGINE is None:
        return _heuristic_decision(features)

    try:
        result: Dict[str, Any] = _FUSION_ENGINE.predict(features, return_breakdown=True, update_history=True)
        decision = result.get("decision_object", {}) or {}
        out = {
            "risk_score": float(decision.get("risk_score", result.get("risk_score", 0.0))),
            "risk_label": str(decision.get("risk_label", result.get("risk_label", "LOW"))),
            "is_attack": bool(decision.get("is_attack", result.get("is_attack", False))),
            "confidence_band": str(decision.get("confidence_band", result.get("confidence_band", "LOW"))),
            "model_consensus": str(decision.get("model_consensus", result.get("model_consensus", "0/0"))),
            "attack_family": str(decision.get("attack_family", result.get("attack_family", "unknown"))),
        }
        return out, result
    except Exception as exc:
        logger.error({"msg": "mutantshield_inference_failed", "error": str(exc)})
        # Model exists but inference failed -> still fail-safe fallback.
        return _heuristic_decision(features)

