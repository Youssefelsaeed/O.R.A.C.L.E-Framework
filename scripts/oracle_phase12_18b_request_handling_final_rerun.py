"""Final request handling rerun gated by runtime-info proof."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

from oracle_phase12_18_common import CORE, ROOT, write_json


def _runtime_ok() -> Dict[str, Any]:
    try:
        runtime = requests.get(f"{CORE}/oracle/runtime-info", timeout=10).json()
        health = requests.get(f"{CORE}/health", timeout=10).json()
        return {"ok": runtime.get("code_marker") == "phase12_18b_runtime" and health.get("code_marker") == "phase12_18b_runtime", "runtime": runtime, "health": health}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _read(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}


def run() -> Dict[str, Any]:
    proof = _runtime_ok()
    if not proof.get("ok"):
        report = {"generated_at": time.time(), "runtime_proof": proof, "status": "BLOCKED_RUNTIME_NOT_CURRENT", "pass": False}
        path = write_json("phase12_18b_request_handling_final_rerun.json", report); report["report_path"] = str(path)
        return report
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "oracle_phase12_17_request_handling_test.py")], cwd=ROOT, text=True, capture_output=True, timeout=1200)
    source = _read(ROOT / "reports" / "final" / "phase12_17_request_handling_test.json")
    metrics = source.get("metrics") or {}
    report: Dict[str, Any] = {"generated_at": time.time(), "runtime_proof": proof, "script_exit_code": proc.returncode, "stdout_tail": proc.stdout[-5000:], "stderr_tail": proc.stderr[-2000:], "metrics": metrics, "root_cause_if_failed": {"failed_services": metrics.get("failed_services"), "valid_degraded": metrics.get("valid_degraded"), "audit_logged_rate": metrics.get("audit_logged_rate"), "local_or_code_blocker": "none" if proc.returncode == 0 else "code_or_service_capacity_blocker"}}
    report["pass"] = proc.returncode == 0
    path = write_json("phase12_18b_request_handling_final_rerun.json", report); report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B REQUEST HANDLING FINAL RERUN ===")
    print(f"Runtime Current Code: {'PASS' if report.get('runtime_proof', {}).get('ok') else 'FAIL'}")
    m = report.get("metrics") or {}
    print(f"valid_failed: {m.get('valid_failed')}")
    print(f"valid_degraded: {m.get('valid_degraded')}")
    print(f"p95_latency_ms: {m.get('p95_latency_ms')}")
    print(f"audit_logged_rate: {m.get('audit_logged_rate')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
