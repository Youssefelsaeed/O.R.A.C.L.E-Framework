"""Realtime replay proof that ORACLE processes live requests now."""
from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "oracle_realtime_replay_proof_report.json"
DEFAULT_CANDIDATES = [
    ROOT / "reports" / "evolution" / "cse_hoic_repair_buffer.csv",
    ROOT / "reports" / "evolution" / "cse_candidate_attack_buffer.csv",
    ROOT / "reports" / "evolution" / "training_buffer_supervised.csv",
]


def _pick_source() -> Path | None:
    for path in DEFAULT_CANDIDATES:
        if path.exists():
            return path
    return None


def _risk_from_label(label: str, idx: int) -> tuple[float, str, bool, str]:
    normalized = (label or "").strip()
    if not normalized or normalized.upper() == "BENIGN":
        return 0.12, "LOW", False, "BENIGN"
    score = 0.92 if idx % 3 else 0.84
    return score, "HIGH", True, normalized


def _event_from_row(row: pd.Series, idx: int) -> Dict[str, Any]:
    label = str(row.get("Label", row.get("label", row.get("attack_family", "BENIGN"))))
    risk_score, risk_label, is_attack, family = _risk_from_label(label, idx)
    return {
        "flow_id": f"replay-{uuid.uuid4().hex}",
        "src_ip": str(row.get("src_ip", row.get("Source IP", f"192.0.2.{idx % 250 + 1}"))),
        "dst_ip": str(row.get("dst_ip", row.get("Destination IP", f"198.51.100.{idx % 250 + 1}"))),
        "risk_score": risk_score,
        "risk_label": risk_label,
        "is_attack": is_attack,
        "attack_family": family,
        "confidence_band": "HIGH" if is_attack else "LOW",
        "model_consensus": "replay-proof",
        "timestamp": time.time(),
    }


def run(events: int = 100, delay_ms: int = 25, oracle_url: str = "http://127.0.0.1:8000") -> Dict[str, Any]:
    source = _pick_source()
    if source and source.exists():
        df = pd.read_csv(source, low_memory=False).head(events)
    else:
        df = pd.DataFrame({"Label": ["BENIGN", "DDOS attack-HOIC", "Brute Force - Web", "SQL Injection"] * max(1, events // 4 + 1)}).head(events)

    endpoint = f"{oracle_url.rstrip()}/oracle/process"
    rows: List[Dict[str, Any]] = []
    counts = {"success": 0, "degraded": 0, "failed": 0}
    started = time.time()
    with requests.Session() as session:
        for idx, (_, row) in enumerate(df.iterrows()):
            payload = _event_from_row(row, idx)
            sent_at = time.time()
            last_error = None
            for attempt in range(1, 4):
                try:
                    response = session.post(endpoint, json=payload, timeout=20)
                    body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    ok = response.status_code in (200, 207)
                    if not ok and response.status_code >= 500 and attempt < 3:
                        time.sleep(0.5 * attempt)
                        continue
                    status = "degraded" if response.status_code == 207 or body.get("status") == "degraded" else "success"
                    if not ok:
                        status = "failed"
                    counts[status] += 1
                    rows.append(
                        {
                            "flow_id": payload["flow_id"],
                            "oracle_trace_id": body.get("oracle_trace_id"),
                            "risk_label": payload["risk_label"],
                            "attack_family": payload["attack_family"],
                            "final_action": (body.get("action") or {}).get("final_action"),
                            "audit_logged": bool((body.get("audit") or {}).get("logged")),
                            "status_code": response.status_code,
                            "attempts": attempt,
                            "latency_ms": round((time.time() - sent_at) * 1000, 2),
                            "timestamp": sent_at,
                            "data_source": "LIVE_REPLAY",
                        }
                    )
                    last_error = None
                    break
                except Exception as exc:
                    last_error = str(exc)
                    if attempt < 3:
                        time.sleep(0.5 * attempt)
                        continue
            if last_error:
                counts["failed"] += 1
                rows.append({"flow_id": payload["flow_id"], "error": last_error, "attempts": 3, "timestamp": sent_at, "data_source": "LIVE_REPLAY"})
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    report = {
        "generated_at": time.time(),
        "source": str(source.relative_to(ROOT)) if source else "synthetic_live_replay_rows",
        "events_requested": events,
        "events_sent": len(rows),
        "counts": counts,
        "trace_ids_generated": sum(1 for row in rows if row.get("oracle_trace_id")),
        "audit_logged_count": sum(1 for row in rows if row.get("audit_logged")),
        "hard_failures": counts["failed"],
        "duration_seconds": round(time.time() - started, 2),
        "events": rows[-50:],
        "pass": len(rows) > 0 and counts["failed"] == 0 and any(row.get("oracle_trace_id") for row in rows),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="ORACLE realtime replay proof")
    parser.add_argument("--events", type=int, default=100)
    parser.add_argument("--delay-ms", type=int, default=25)
    parser.add_argument("--oracle-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    report = run(events=args.events, delay_ms=args.delay_ms, oracle_url=args.oracle_url)
    print("\n=== ORACLE REALTIME REPLAY PROOF ===")
    print(f"Events Sent: {report['events_sent']}")
    print(f"Success: {report['counts']['success']}")
    print(f"Degraded: {report['counts']['degraded']}")
    print(f"Failed: {report['counts']['failed']}")
    print(f"Trace IDs: {report['trace_ids_generated']}")
    print(f"Audit Logged: {report['audit_logged_count']}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
