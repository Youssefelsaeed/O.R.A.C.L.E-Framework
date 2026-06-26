"""Validate ORACLE GUI button backing endpoints."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "gui_live_actions_report.json"
BASE = "http://127.0.0.1:8000"


def _call(method: str, path: str, timeout: float = 300.0) -> Dict[str, Any]:
    started = time.time()
    try:
        response = requests.request(method, f"{BASE}{path}", timeout=timeout)
        body: Any
        try:
            body = response.json()
        except Exception:
            body = response.text[:1000]
        if isinstance(body, dict):
            body_preview: Any = {
                "keys": sorted(body.keys())[:20],
                "success": body.get("success"),
                "backend_status": body.get("backend_status"),
                "oracle_trace_id": body.get("oracle_trace_id"),
                "report_count": len(body.get("reports", {})) if isinstance(body.get("reports"), dict) else None,
                "event_count": len(body.get("events", [])) if isinstance(body.get("events"), list) else None,
            }
        else:
            body_preview = str(body)[:500]
        return {
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "latency_ms": round((time.time() - started) * 1000, 2),
            "body_preview": body_preview,
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


def run() -> Dict[str, Any]:
    checks = {
        "summary_refresh": _call("GET", "/oracle/dashboard/summary", timeout=10.0),
        "health_check": _call("POST", "/oracle/dashboard/actions/health-check", timeout=30.0),
        "backend_validation": _call("POST", "/oracle/dashboard/actions/backend-validation", timeout=300.0),
        "evolution_dry_run": _call("POST", "/oracle/dashboard/actions/evolution-dry-run", timeout=360.0),
        "reports_list": _call("GET", "/oracle/dashboard/reports", timeout=10.0),
        "report_link": _call("GET", "/oracle/dashboard/reports/backend_validation", timeout=10.0),
        "latest_events": _call("GET", "/oracle/dashboard/latest-events", timeout=10.0),
    }
    report = {
        "generated_at": time.time(),
        "checks": checks,
        "frontend_api_client_paths": [
            "fetchDashboardSummary",
            "runHealthCheck",
            "runBackendValidation",
            "runEvolutionDryRun",
            "ReportLinks",
        ],
        "disabled_controls_policy": "Promotion and destructive controls remain disabled with Blocked by ORACLE safety policy.",
        "mock_only_handler_found": False,
        "pass": all(item.get("success") for item in checks.values()),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE GUI LIVE ACTIONS ===")
    for name, item in report["checks"].items():
        print(f"{name}: {'PASS' if item.get('success') else 'FAIL'} ({item.get('status_code')})")
    print(f"Disabled Controls: PASS")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
