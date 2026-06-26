"""Shared helpers for ORACLE Phase 8 full framework testing."""
from __future__ import annotations

import hashlib
import json
import statistics
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
PHASE8_DIR = ROOT / "reports" / "phase8"
MODELS_FINAL = ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "models_final"
GUI_DIR = ROOT / "O.R.A.C.L.E_GUi_V1_Figma"
ORACLE_URL = "http://127.0.0.1:8000/oracle/process"

SAMPLE_FEATURES = {
    "Destination Port": 80.0,
    "Flow Duration": 500.0,
    "Total Fwd Packets": 10.0,
    "Total Backward Packets": 5.0,
    "Total Length of Fwd Packets": 1200.0,
    "Total Length of Bwd Packets": 600.0,
    "Fwd Packet Length Mean": 120.0,
    "Bwd Packet Length Mean": 120.0,
    "Flow Bytes/s": 3600.0,
    "Flow Packets/s": 30.0,
}

QAUTH_TRANSITIONS = ROOT / "reports" / "qauth_assurance_transitions.jsonl"
CHRONO_TRANSITIONS = ROOT / "reports" / "chrono_assurance_transitions.jsonl"
ETHICQ_TRANSITIONS = ROOT / "reports" / "ethicq_provenance_transitions.jsonl"
JOBS_JSONL = ROOT / "reports" / "ghosttunnel_transmit_jobs.jsonl"


def pf(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def production_model_hashes() -> Dict[str, str]:
    if not MODELS_FINAL.exists():
        return {}
    out: Dict[str, str] = {}
    for f in MODELS_FINAL.rglob("*"):
        if f.is_file():
            out[str(f.relative_to(MODELS_FINAL))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def write_phase8_report(name: str, data: Dict[str, Any]) -> Path:
    PHASE8_DIR.mkdir(parents=True, exist_ok=True)
    path = PHASE8_DIR / name
    data.setdefault("generated_at", time.time())
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def oracle_payload(**overrides: Any) -> Dict[str, Any]:
    base = {
        "flow_id": f"phase8-{uuid.uuid4().hex[:8]}",
        "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.50",
        "risk_score": 0.42,
        "risk_label": "LOW",
        "is_attack": False,
        "attack_family": "benign",
        "confidence_band": "LOW",
        "model_consensus": "3/4",
    }
    base.update(overrides)
    return base


def post_oracle(payload: Dict[str, Any], timeout: float = 30.0) -> Tuple[Optional[int], Dict[str, Any], float, Optional[str]]:
    t0 = time.perf_counter()
    try:
        r = requests.post(ORACLE_URL, json=payload, timeout=timeout)
        body = r.json() if r.content else {}
        return r.status_code, body, round((time.perf_counter() - t0) * 1000.0, 2), None
    except Exception as exc:
        return None, {}, round((time.perf_counter() - t0) * 1000.0, 2), str(exc)


def percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = int(round((pct / 100.0) * (len(values) - 1)))
    return values[max(0, min(idx, len(values) - 1))]


def latest_assurance_stats() -> Dict[str, int]:
    rows = read_jsonl(QAUTH_TRANSITIONS) + read_jsonl(CHRONO_TRANSITIONS) + read_jsonl(ETHICQ_TRANSITIONS)
    latest: Dict[tuple[str, str], Dict[str, Any]] = {}
    for row in rows:
        trace_id = str(row.get("trace_id", ""))
        component = str(row.get("component", ""))
        if not trace_id or not component:
            continue
        key = (trace_id, component)
        ts = float(row.get("updated_at", 0) or 0)
        prev = latest.get(key)
        if prev is None or ts >= float(prev.get("updated_at", 0) or 0):
            latest[key] = row
    completed = sum(1 for r in latest.values() if str(r.get("status", "")).lower() == "completed")
    failed = sum(1 for r in latest.values() if str(r.get("status", "")).lower() == "failed")
    pending = sum(
        1 for r in latest.values() if str(r.get("status", "")).lower() in ("queued", "pending", "processing", "provisional")
    )
    return {
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "total": len(latest),
    }


def latest_job_stats() -> Dict[str, int]:
    rows = read_jsonl(JOBS_JSONL)
    latest: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        jid = str(row.get("transmit_job_id", ""))
        if not jid:
            continue
        ts = float(row.get("updated_at", 0) or 0)
        prev = latest.get(jid)
        if prev is None or ts >= float(prev.get("updated_at", 0) or 0):
            latest[jid] = row
    completed = sum(1 for j in latest.values() if j.get("status") == "transmitted")
    failed = sum(1 for j in latest.values() if j.get("status") == "failed")
    pending = sum(1 for j in latest.values() if j.get("status") in ("queued", "processing", "provisional"))
    return {"completed": completed, "failed": failed, "pending": pending, "total": len(latest)}


def wait_assurance_completion(timeout_s: float = 60.0) -> Dict[str, int]:
    deadline = time.time() + timeout_s
    stats = latest_assurance_stats()
    while time.time() < deadline:
        stats = latest_assurance_stats()
        if stats["pending"] == 0:
            return stats
        time.sleep(1)
    return stats


def service_get(url: str, timeout: float = 5.0) -> Tuple[Optional[int], Any]:
    try:
        r = requests.get(url, timeout=timeout)
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, r.text
    except Exception as exc:
        return None, str(exc)
