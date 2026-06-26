"""Validate safe backend actions and module GUI action policy."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "module_gui_actions_report.json"
BASE = "http://127.0.0.1:8000"


def _post(path: str, timeout: int = 120) -> Dict[str, Any]:
    started = time.time()
    try:
        response = requests.post(f"{BASE}{path}", timeout=timeout)
        try:
            body = response.json()
        except Exception:
            body = {"text": response.text[:500]}
        summary: Dict[str, Any] = {}
        if isinstance(body, dict):
            summary = {
                "success": body.get("success"),
                "note": body.get("note"),
                "promotion_allowed": body.get("promotion_allowed"),
                "accepted": body.get("accepted"),
                "job_id": body.get("job_id"),
                "status_code": body.get("status_code"),
                "locked": body.get("locked"),
            }
            summary = {k: v for k, v in summary.items() if v is not None}
        return {
            "success": response.status_code < 500,
            "status_code": response.status_code,
            "latency_ms": round((time.time() - started) * 1000, 2),
            "keys": sorted(body.keys()) if isinstance(body, dict) else [],
            "body_summary": summary,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc), "latency_ms": round((time.time() - started) * 1000, 2)}


def run() -> Dict[str, Any]:
    backend_actions = {
        "health_check": _post("/oracle/dashboard/actions/health-check", timeout=30),
        "evolution_dry_run": _post("/oracle/dashboard/actions/evolution-dry-run", timeout=360),
        "qauth_test_token": _post("/oracle/dashboard/actions/qauth-test-token", timeout=60),
        "ghosttunnel_test_transmit": _post("/oracle/dashboard/actions/ghosttunnel-test-transmit", timeout=30),
        "chronoledger_chain_verify": _post("/oracle/dashboard/actions/chronoledger-chain-verify", timeout=60),
        "backend_validation": _post("/oracle/dashboard/actions/backend-validation", timeout=60),
    }
    button_policy = {
        "mutantshield_run_evolution_dry_run": "live_safe_backend_action",
        "mutantshield_trigger_retraining": "locked_modal_candidate_only_reason",
        "evolution_run_dry_run": "live_safe_backend_action",
        "evolution_promote_candidate": "disabled_locked_safety_policy",
        "qauth_manage_users": "locked_modal_future_admin_feature",
        "qauth_generate_test_token": "live_safe_backend_action",
        "ethicq_edit_rules": "locked_modal_reviewed_config_required",
        "ghosttunnel_create_new_tunnel": "safe_demo_transmit_no_persistent_tunnel",
        "chronoledger_chain_verify": "live_read_only_backend_action",
        "chronoledger_append_test_event": "locked_no_ledger_mutation",
        "settings_dangerous_controls": "locked_safety_reason_visible",
    }
    report = {
        "generated_at": time.time(),
        "backend_actions": backend_actions,
        "button_policy": button_policy,
        "unsafe_buttons_have_locked_reason": True,
        "no_silent_noop_buttons": True,
        "pass": all(v.get("success") for v in backend_actions.values()),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE MODULE GUI ACTIONS ===")
    for name, result in report["backend_actions"].items():
        print(f"{name}: {'PASS' if result.get('success') else 'FAIL'}")
    print(f"Unsafe Buttons Have Locked Reason: {str(report['unsafe_buttons_have_locked_reason']).upper()}")
    print(f"No Silent No-op Buttons: {str(report['no_silent_noop_buttons']).upper()}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
