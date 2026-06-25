"""Production ensemble model discovery and coverage reporting."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import EvolutionConfig
from .reports import write_json

ENSEMBLE_MODELS = (
    "XGBoost",
    "AutoEncoder",
    "LSTM",
    "GNN",
    "FusionMLP",
    "GAN",
)

PRODUCTION_DIRS = {
    "XGBoost": "XGboost",
    "AutoEncoder": "AutoEncoder",
    "LSTM": "LSTM_Optimized",
    "GNN": "GNN",
    "FusionMLP": "FusionEngine",
    "GAN": "GAN",
}

CANDIDATE_DIRS = {
    "XGBoost": "XGboost",
    "AutoEncoder": "AutoEncoder",
    "LSTM": "LSTM_Optimized",
    "GNN": "GNN",
    "FusionMLP": "FusionEngine",
    "GAN": "GAN",
}

PRODUCTION_MARKERS = {
    "XGBoost": ["xgboost_classifier.pkl", "**/xgboost_classifier.pkl"],
    "AutoEncoder": ["autoencoder_v1.pkl", "**/autoencoder_v1.pkl"],
    "LSTM": ["**/lstm_v2_final*.pkl", "**/lstm_v2_metadata.pkl"],
    "GNN": ["gnn_graphsage_mutantshield.pth", "gnn_graphsage_builder.pkl"],
    "FusionMLP": ["learned_fusion_mlp.pt"],
    "GAN": ["generator*.pt", "gan_metadata.json", "scaler.pkl"],
}


def _find_artifact(base: Path, patterns: List[str]) -> Optional[Path]:
    if not base.exists():
        return None
    for pat in patterns:
        hits = sorted(base.glob(pat))
        if hits:
            return hits[0]
    return None


def discover_production_artifacts(cfg: EvolutionConfig) -> Dict[str, Optional[str]]:
    prod = cfg.models_final_dir
    out: Dict[str, Optional[str]] = {}
    for name in ENSEMBLE_MODELS:
        sub = prod / PRODUCTION_DIRS[name]
        art = _find_artifact(sub, PRODUCTION_MARKERS[name])
        if art is None and name == "LSTM":
            art = _find_artifact(prod / "LSTM_Optimized", PRODUCTION_MARKERS[name])
        out[name] = str(art) if art else None
    return out


def empty_model_entry(model_name: str) -> Dict[str, Any]:
    return {
        "model_name": model_name,
        "production_artifact_found": False,
        "production_artifact_path": None,
        "candidate_training_attempted": False,
        "candidate_trained": False,
        "retraining_supported": True,
        "adversarial_evaluated": False,
        "adversarial_training_applied": False,
        "promotion_eligible": False,
        "blocker_reason": None,
        "candidate_artifact_path": None,
        "status": "pending",
    }


def build_coverage_report(
    cfg: EvolutionConfig,
    model_results: List[Dict[str, Any]],
    *,
    candidate_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    production = discover_production_artifacts(cfg)
    by_name = {m["model_name"]: m for m in model_results}
    models: List[Dict[str, Any]] = []
    for name in ENSEMBLE_MODELS:
        entry = dict(by_name.get(name, empty_model_entry(name)))
        entry["model_name"] = name
        entry["production_artifact_found"] = production.get(name) is not None
        entry["production_artifact_path"] = production.get(name)
        if not entry.get("blocker_reason") and not entry.get("candidate_trained"):
            if name == "GAN":
                entry["blocker_reason"] = "gan_not_trained"
                entry["retraining_supported"] = False
                entry["status"] = "not_trained"
            elif not entry.get("candidate_training_attempted"):
                entry["status"] = "not_attempted"
        models.append(entry)

    promotion_eligible = [m for m in models if m.get("promotion_eligible")]
    trained = [m for m in models if m.get("candidate_trained")]
    real_trained = [
        m
        for m in models
        if m.get("candidate_trained")
        and m.get("status") in ("trained", "real_trained", "candidate_validated")
        and not m.get("surrogate_used")
        and str(m.get("status")) != "surrogate_trained"
    ]
    required_real = ("XGBoost", "AutoEncoder", "LSTM", "GNN")
    missing_required = [
        m
        for m in models
        if m.get("model_name") in required_real
        and not (
            m.get("candidate_trained")
            and m.get("status") in ("trained", "real_trained", "candidate_validated")
            and not m.get("surrogate_used")
        )
    ]
    report = {
        "generated_at": time.time(),
        "candidate_dir": str(candidate_dir) if candidate_dir else None,
        "models": models,
        "models_trained_count": len(trained),
        "real_models_trained_count": len(real_trained),
        "promotion_eligible_count": len(promotion_eligible),
        "full_ensemble_complete": len(missing_required) == 0,
        "framework_final": True,
        "framework_final_with_limitations": len(missing_required) > 0,
        "ensemble_limitations": [
            {
                "model_name": m.get("model_name"),
                "status": m.get("status"),
                "blocker_reason": m.get("blocker_reason"),
                "production_inference_available": m.get("production_artifact_found"),
                "safe_to_train": m.get("safe_to_train"),
                "contract_validation": m.get("contract_validation"),
            }
            for m in missing_required
        ],
        "contract_gated_models": [
            {
                "model_name": m.get("model_name"),
                "status": m.get("status"),
                "safe_to_train": m.get("safe_to_train"),
                "missing_columns": (m.get("contract_validation") or {}).get("missing_columns", []),
            }
            for m in models
            if str(m.get("status", "")).startswith("blocked_contract")
        ],
        "ensemble_promotion_ready": False if missing_required else (all(m.get("promotion_eligible") for m in promotion_eligible) if promotion_eligible else False),
    }
    path = cfg.reports_dir / "model_coverage_report.json"
    write_json(path, report)
    if candidate_dir:
        write_json(candidate_dir / "model_coverage_report.json", report)
    return report
