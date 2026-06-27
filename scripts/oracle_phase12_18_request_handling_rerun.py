"""Phase 12.18 strict request-handling rerun wrapper."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

from oracle_phase12_18_common import ROOT, write_json


def _read(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}


def run() -> Dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "oracle_phase12_17_request_handling_test.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=1200,
    )
    source = _read(ROOT / "reports" / "final" / "phase12_17_request_handling_test.json")
    metrics = source.get("metrics") or {}
    pass_checks = source.get("pass_checks") or {}
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "duration_seconds": round(time.time() - started, 2),
        "script_exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-5000:],
        "stderr_tail": proc.stderr[-2000:],
        "source_report": "reports/final/phase12_17_request_handling_test.json",
        "metrics": metrics,
        "pass_checks": pass_checks,
        "failed_service_distribution": metrics.get("failed_services") or {},
        "degraded_causes": {
            "failed_services": metrics.get("failed_services") or {},
            "audit_logged_rate": metrics.get("audit_logged_rate"),
            "p95_latency_ms": metrics.get("p95_latency_ms"),
            "client_p95_latency_ms": metrics.get("client_p95_latency_ms"),
        },
        "pass_targets": {
            "valid_failed_zero": metrics.get("valid_failed") == 0,
            "degraded_under_or_equal_1pct": (metrics.get("valid_degraded", 0) / max(1, metrics.get("valid_total", 0))) <= 0.01,
            "p95_under_1000_preferred": (metrics.get("p95_latency_ms") or 999999) <= 1000,
            "audit_logged_at_least_99pct": (metrics.get("audit_logged_rate") or 0) >= 0.99,
            "assurance_pending_latest_zero": metrics.get("assurance_latest_pending") == 0,
        },
    }
    report["pass"] = proc.returncode == 0 and all(report["pass_targets"].values())
    path = write_json("phase12_18_request_handling_rerun.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18 REQUEST HANDLING RERUN ===")
    m = report["metrics"]
    print(f"valid_failed: {m.get('valid_failed')}")
    print(f"valid_degraded: {m.get('valid_degraded')}")
    print(f"p95_latency_ms: {m.get('p95_latency_ms')}")
    print(f"audit_logged_rate: {m.get('audit_logged_rate')}")
    print(f"failed_services: {report['failed_service_distribution']}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
