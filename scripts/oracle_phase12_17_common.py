"""Shared helpers for Phase 12.17 operational verification."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "final"
MODELS_FINAL = ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "models_final"

CORE = "http://127.0.0.1:8000"
QAUTH = "http://127.0.0.1:8001"
ETHICQ = "http://127.0.0.1:8002"
CHRONO = "http://127.0.0.1:8003"
GHOST = "http://127.0.0.1:8004"
GUI = "http://127.0.0.1:4173"


def write_report(name: str, report: Dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / name
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def timed_request(method: str, url: str, *, json_body: Any | None = None, timeout: float = 30.0) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        response = requests.request(method, url, json=json_body, timeout=timeout)
        latency = round((time.perf_counter() - started) * 1000, 2)
        try:
            body = response.json()
        except Exception:
            body = {"text": response.text[:500]}
        return {
            "method": method,
            "url": url,
            "status_code": response.status_code,
            "latency_ms": latency,
            "success": response.status_code < 500,
            "response_keys": sorted(body.keys())[:25] if isinstance(body, dict) else [],
            "body_summary": summarize_body(body),
        }
    except Exception as exc:
        return {
            "method": method,
            "url": url,
            "status_code": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "success": False,
            "error": str(exc),
        }


def summarize_body(body: Any) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {}
    summary = {
        "status": body.get("status"),
        "service": body.get("service"),
        "backend_status": body.get("backend_status"),
        "success": body.get("success"),
        "oracle_trace_id": body.get("oracle_trace_id"),
        "audit_logged": bool((body.get("audit") or {}).get("logged")) if isinstance(body.get("audit"), dict) else body.get("audit_logged"),
        "failed_services": body.get("failed_services"),
        "promotion_allowed": body.get("promotion_allowed"),
        "events": len(body.get("events", [])) if isinstance(body.get("events"), list) else None,
    }
    return {key: value for key, value in summary.items() if value is not None}


def sample_payload(kind: str = "high_attack", idx: int = 0) -> Dict[str, Any]:
    base = {
        "flow_id": f"phase12-17-{kind}-{idx}-{int(time.time() * 1000)}",
        "src_ip": f"192.0.2.{idx % 250 + 1}",
        "dst_ip": f"198.51.100.{idx % 250 + 1}",
        "confidence_band": "HIGH",
        "model_consensus": "phase12.17",
        "timestamp": time.time(),
    }
    if kind == "benign":
        return {**base, "risk_score": 0.12, "risk_label": "LOW", "is_attack": False, "attack_family": "BENIGN", "confidence_band": "LOW"}
    if kind == "medium":
        return {**base, "risk_score": 0.55, "risk_label": "MEDIUM", "is_attack": True, "attack_family": "uncertain_behavior", "confidence_band": "MEDIUM"}
    if kind == "dohbrw":
        return {**base, "risk_score": 0.88, "risk_label": "HIGH", "is_attack": True, "attack_family": "DoHBrw anomaly", "doh_query_entropy": 4.8}
    return {**base, "risk_score": 0.93, "risk_label": "HIGH", "is_attack": True, "attack_family": "DDoS"}


def model_hashes() -> Dict[str, str]:
    if not MODELS_FINAL.exists():
        return {}
    hashes: Dict[str, str] = {}
    for path in MODELS_FINAL.rglob("*"):
        if path.is_file():
            hashes[str(path.relative_to(MODELS_FINAL)).replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def run_python_script(script_name: str, *args: str, timeout: int = 900) -> Dict[str, Any]:
    started = time.time()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "success": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-2000:],
        "duration_seconds": round(time.time() - started, 2),
    }


def all_ok(items: Iterable[Dict[str, Any]]) -> bool:
    return all(bool(item.get("success")) for item in items)
