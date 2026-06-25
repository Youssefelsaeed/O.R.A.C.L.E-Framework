"""Extract operational evidence from ChronoLedger / ORACLE reports without trusting labels."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import EvolutionConfig
from .reports import read_json, write_json

ROOT = Path(__file__).resolve().parents[2]


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
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


def _classify_bucket(ev: Dict[str, Any]) -> str:
    risk = float(ev.get("risk_score", 0) or 0)
    is_attack = bool(ev.get("is_attack", False))
    ethics = str(ev.get("ethics_decision", "") or "").lower()
    action = str(ev.get("action_final_action", "") or "").lower()
    human = bool(ev.get("human_reviewed", False))

    if human:
        if is_attack and action in ("allow",):
            return "false_negative_candidate"
        if not is_attack and action in ("block", "investigate"):
            return "false_positive_candidate"

    if risk >= 0.8 and is_attack:
        return "high_confidence_attack"
    if risk <= 0.2 and not is_attack:
        return "high_confidence_benign"
    if ethics == "investigate" and not is_attack and risk >= 0.5:
        return "false_positive_candidate"
    if is_attack and action == "allow":
        return "false_negative_candidate"
    if risk >= 0.95 or risk <= 0.05:
        return "outlier_candidate"
    if bool(ev.get("ethics_requires_human_review", False)):
        return "human_review_required"
    return "outlier_candidate"


def _normalize_event(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    detection = raw.get("detection") or {}
    ethics = raw.get("ethics") or {}
    action = raw.get("action") or {}
    audit = raw.get("audit") or {}
    network = raw.get("network") or {}
    assurance = raw.get("assurance_states") or {}
    human_reviewed = bool(raw.get("human_reviewed", False) or ethics.get("human_reviewed", False))
    ev = {
        "oracle_trace_id": raw.get("oracle_trace_id"),
        "flow_id": network.get("flow_id") or raw.get("flow_id"),
        "src_ip": network.get("src_ip") or raw.get("src_ip"),
        "dst_ip": network.get("dst_ip") or raw.get("dst_ip"),
        "risk_score": detection.get("risk_score", raw.get("risk_score")),
        "risk_label": detection.get("risk_label", raw.get("risk_label")),
        "is_attack": detection.get("is_attack", raw.get("is_attack")),
        "attack_family": detection.get("attack_family", raw.get("attack_family")),
        "ethics_decision": ethics.get("decision"),
        "ethics_requires_human_review": ethics.get("requires_human_review"),
        "action_final_action": action.get("final_action"),
        "action_executed": action.get("executed"),
        "audit_ledger_event_id": audit.get("ledger_event_id"),
        "assurance_states": assurance,
        "timestamp": raw.get("timestamp", time.time()),
        "human_reviewed": human_reviewed,
        "label_trust": "verified" if human_reviewed else "unverified",
        "source": raw.get("_source", "report"),
    }
    ev["evidence_bucket"] = _classify_bucket(ev)
    return ev


def _from_oracle_reports() -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    report_paths = [
        ROOT / "reports" / "oracle_backend_final_validation.json",
        ROOT / "reports" / "async_assurance_stress_100.json",
        ROOT / "reports" / "async_assurance_integrity.json",
    ]
    for rp in report_paths:
        if not rp.exists():
            continue
        data = read_json(rp)
        for key in ("events", "all_requests"):
            for item in data.get(key, []) or []:
                raw = item.get("oracle_event") or item
                if isinstance(raw, dict):
                    raw = {**raw, "_source": rp.name}
                    ev = _normalize_event(raw)
                    if ev:
                        events.append(ev)
        for section in ("baseline_20_events", "failure_test_10_events"):
            sec = data.get(section) or {}
            for item in sec.get("events", []) or []:
                raw = item.get("oracle_event") or item
                if isinstance(raw, dict):
                    raw = {**raw, "_source": rp.name}
                    ev = _normalize_event(raw)
                    if ev:
                        events.append(ev)
        if "ghosttunnel_benchmark" in data:
            for item in (data["ghosttunnel_benchmark"].get("fast_ack") or {}).get("sample_records", []):
                pass  # samples lack full oracle_event; skip
    return events


def _from_chrono_sqlite() -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    db_paths = [
        ROOT / "Chrono_Ledger Module" / "data" / "chronoledger.db",
        ROOT / "reports" / "chronoledger.db",
    ]
    for db in db_paths:
        if not db.exists():
            continue
        try:
            conn = sqlite3.connect(str(db))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            for table in tables:
                if "event" in table.lower():
                    try:
                        cur.execute(f"SELECT * FROM {table} LIMIT 200")
                        cols = [d[0] for d in cur.description]
                        for row in cur.fetchall():
                            rec = dict(zip(cols, row))
                            data_field = rec.get("data") or rec.get("payload")
                            if isinstance(data_field, str):
                                try:
                                    data_field = json.loads(data_field)
                                except json.JSONDecodeError:
                                    data_field = {}
                            if isinstance(data_field, dict):
                                data_field["_source"] = "chrono_sqlite"
                                ev = _normalize_event(data_field)
                                if ev:
                                    events.append(ev)
                    except Exception:
                        continue
            conn.close()
        except Exception:
            continue
    return events


def extract_chronoledger_evidence(cfg: EvolutionConfig) -> Dict[str, Any]:
    events = _from_oracle_reports()
    if cfg.use_chronoledger:
        events.extend(_from_chrono_sqlite())

    # Deduplicate by trace_id + flow_id
    seen = set()
    unique: List[Dict[str, Any]] = []
    for ev in events:
        key = (str(ev.get("oracle_trace_id")), str(ev.get("flow_id")))
        if key in seen:
            continue
        seen.add(key)
        unique.append(ev)

    buckets: Dict[str, int] = {}
    for ev in unique:
        b = ev.get("evidence_bucket", "unknown")
        buckets[b] = buckets.get(b, 0) + 1

    report = {
        "generated_at": time.time(),
        "total_events": len(unique),
        "bucket_counts": buckets,
        "require_human_approval_for_chrono": cfg.require_human_approval_for_chrono,
        "events": unique,
    }
    out = cfg.reports_dir / "chronoledger_evidence.json"
    write_json(out, report)
    return report
