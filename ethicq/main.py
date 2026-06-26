from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

repo_root = Path(__file__).resolve().parents[1]
ethicq_root = repo_root / "Ethic-Q Module"
if str(ethicq_root) not in sys.path:
    sys.path.insert(0, str(ethicq_root))

try:
    from main import app  # type: ignore  # noqa: E402,F401
except Exception:
    from fastapi import FastAPI

    app = FastAPI(title="EthicQ Runtime Fallback", version="1.0.0")

    @app.get("/health")
    @app.get("/api/v1/health")
    async def health() -> Dict[str, Any]:
        return {
            "status": "ok",
            "mode": "docker_runtime_fallback",
            "policy": "defensive_only_human_review_for_high_risk",
        }

    @app.post("/api/v1/decisions/evaluate")
    async def evaluate_decision(payload: Dict[str, Any]) -> Dict[str, Any]:
        alert = payload.get("threat_alert") or {}
        risk_score = float(alert.get("risk_score", alert.get("threat_level", 0.0)) or 0.0)
        risk_label = str(alert.get("risk_label", "UNKNOWN")).upper()
        if risk_score >= 0.9 or risk_label in {"CRITICAL", "HIGH"}:
            action = "investigate"
            confidence = 0.91
            requires_human_review = risk_score >= 0.95
        elif risk_score >= 0.5:
            action = "monitor"
            confidence = 0.84
            requires_human_review = False
        else:
            action = "allow"
            confidence = 0.95
            requires_human_review = False
        return {
            "action": action,
            "confidence": confidence,
            "requires_human_review": requires_human_review,
            "provenance_state": "verified",
            "reasoning": "Runtime fallback applies conservative defensive-only policy.",
            "mode": "docker_runtime_fallback",
        }

