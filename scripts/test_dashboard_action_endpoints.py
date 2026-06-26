"""Validate live dashboard action endpoints for the operator GUI."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "dashboard_action_endpoints_report.json"
BASE = "http://127.0.0.1:8000"


def _request(method: str, path: str, timeout: float = 180.0) -> Dict[str, Any]:
    started = time.time()
    try:
        response = requests.request(method, f"{BASE}{path}", timeout=timeout)
        try:
            body = response.json()
        except Exception:
            body = {"text": response.text[:500]}
        return {
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "latency_ms": round((time.time() - started) * 1000, 2),
            "keys": sorted(body.keys())[:20] if isinstance(body, dict) else [],
            "summary": _summarize_body(body),
        }
    except Exception as exc:
        return {
            "method": method,
            "path": path,
            "status_code": None,
            "success": False,
            "latency_ms": round((time.time() - started) * 1000, 2),
            "error": str(exc),
        }


def _summarize_body(body: Any) -> Dict[str, Any]:
    if not isinstance(body, dict):
        return {}
    return {
        "backend_status": body.get("backend_status"),
        "success": body.get("success"),
        "oracle_trace_id": body.get("oracle_trace_id"),
        "audit_logged": body.get("audit_logged"),
        "events": len(body.get("events", [])) if isinstance(body.get("events"), list) else None,
        "reports": len(body.get("reports", {})) if isinstance(body.get("reports"), dict) else None,
        "promotion_allowed": body.get("promotion_allowed"),
    }


def run() -> Dict[str, Any]:
    checks = {
        "summary": _request("GET", "/oracle/dashboard/summary", timeout=10),
        "latest_events": _request("GET", "/oracle/dashboard/latest-events", timeout=10),
        "health_check": _request("POST", "/oracle/dashboard/actions/health-check", timeout=30),
        "backend_validation": _request("POST", "/oracle/dashboard/actions/backend-validation", timeout=60),
        "evolution_dry_run": _request("POST", "/oracle/dashboard/actions/evolution-dry-run", timeout=360),
        "reports": _request("GET", "/oracle/dashboard/reports", timeout=10),
        "report_backend_validation": _request("GET", "/oracle/dashboard/reports/backend_validation", timeout=10),
    }
    report = {
        "generated_at": time.time(),
        "base_url": BASE,
        "checks": checks,
        "pass": all(check.get("success") for check in checks.values()),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE DASHBOARD ACTION ENDPOINTS ===")
    for name, check in report["checks"].items():
        print(f"{name}: {'PASS' if check.get('success') else 'FAIL'} ({check.get('status_code')})")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
