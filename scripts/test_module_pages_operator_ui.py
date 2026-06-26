"""Validate module operator UI source labels, replay visibility, and GUI build."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / "O.R.A.C.L.E_GUi_V1_Figma"
REPORT = ROOT / "reports" / "final" / "module_pages_operator_ui_report.json"
BASE = "http://127.0.0.1:8000"


def _get(path: str) -> Dict[str, Any]:
    try:
        response = requests.get(f"{BASE}{path}", timeout=20)
        return {"success": response.status_code < 500, "status_code": response.status_code}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _post(path: str) -> Dict[str, Any]:
    try:
        response = requests.post(f"{BASE}{path}", timeout=60)
        return {"success": response.status_code < 500, "status_code": response.status_code}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _source_labels_present() -> Dict[str, bool]:
    components = [
        "mutant-shield.tsx",
        "qauth-core.tsx",
        "ethic-q.tsx",
        "ghost-tunnel.tsx",
        "chrono-ledger.tsx",
        "settings-page.tsx",
        "global-dashboard.tsx",
        "ai-lifecycle.tsx",
    ]
    result: Dict[str, bool] = {}
    for component in components:
        text = (GUI / "src" / "app" / "components" / component).read_text(encoding="utf-8")
        result[component] = any(label in text for label in ("DataBadge", "SourceLabel", "LOCKED", "REPORT", "DEMO", "LIVE"))
    return result


def run() -> Dict[str, Any]:
    replay = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "oracle_realtime_replay_proof.py"), "--events", "10"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        timeout=240,
    )
    latest = requests.get(f"{BASE}/oracle/dashboard/latest-events", timeout=20).json()
    events = latest.get("events") or []
    latest_visible = any("LIVE_REPLAY" in str(event.get("data_source", "")) for event in events)
    endpoints = {
        "module_status": _get("/oracle/dashboard/module-status"),
        "latest_events": _get("/oracle/dashboard/latest-events"),
        "health_check": _post("/oracle/dashboard/actions/health-check"),
        "ghosttunnel_test_transmit": _post("/oracle/dashboard/actions/ghosttunnel-test-transmit"),
        "chronoledger_chain_verify": _post("/oracle/dashboard/actions/chronoledger-chain-verify"),
        "qauth_test_token": _post("/oracle/dashboard/actions/qauth-test-token"),
    }
    npm = "npm.cmd" if os.name == "nt" else "npm"
    build = subprocess.run([npm, "run", "build"], cwd=str(GUI), text=True, capture_output=True, timeout=240)
    labels = _source_labels_present()
    report = {
        "generated_at": time.time(),
        "gui_reachable": _get("/docs").get("success"),
        "dashboard_live_mode_visible_in_source": "Data Mode" in (GUI / "src" / "app" / "components" / "global-dashboard.tsx").read_text(encoding="utf-8"),
        "replay_exit_code": replay.returncode,
        "latest_events_visible_after_replay": latest_visible,
        "latest_event_count": len(events),
        "module_action_endpoints": endpoints,
        "module_data_source_labels": labels,
        "gui_build": {"success": build.returncode == 0, "exit_code": build.returncode, "stderr_tail": build.stderr[-1000:]},
    }
    report["pass"] = (
        replay.returncode == 0
        and latest_visible
        and all(v.get("success") for v in endpoints.values())
        and all(labels.values())
        and report["gui_build"]["success"]
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE MODULE PAGES OPERATOR UI ===")
    print(f"Replay Proof: {'PASS' if report['replay_exit_code'] == 0 else 'FAIL'}")
    print(f"Latest Events Visible: {'PASS' if report['latest_events_visible_after_replay'] else 'FAIL'}")
    print(f"Module Endpoints: {'PASS' if all(v.get('success') for v in report['module_action_endpoints'].values()) else 'FAIL'}")
    print(f"Data Source Labels: {'PASS' if all(report['module_data_source_labels'].values()) else 'FAIL'}")
    print(f"GUI Build: {'PASS' if report['gui_build']['success'] else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
