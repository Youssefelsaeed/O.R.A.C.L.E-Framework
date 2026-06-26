"""Validate the GUI operator console has live backend evidence available."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Set

import requests

ROOT = Path(__file__).resolve().parents[1]
GUI_DIR = ROOT / "O.R.A.C.L.E_GUi_V1_Figma"
REPORT = ROOT / "reports" / "final" / "gui_operator_console_live_report.json"
BACKEND = "http://127.0.0.1:8000"
GUI = "http://127.0.0.1:4173"


def _get_json(path: str) -> Dict[str, Any]:
    response = requests.get(f"{BACKEND}{path}", timeout=10)
    response.raise_for_status()
    return response.json()


def _trace_ids() -> Set[str]:
    data = _get_json("/oracle/dashboard/latest-events")
    return {
        str(event.get("oracle_trace_id"))
        for event in data.get("events", [])
        if event.get("oracle_trace_id")
    }


def _probe(url: str) -> Dict[str, Any]:
    try:
        response = requests.get(url, timeout=10)
        return {"success": response.status_code < 500, "status_code": response.status_code}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _run_script(*args: str, timeout: int = 600, cwd: Path | None = None) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            list(args),
            cwd=str(cwd or ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-5000:],
            "stderr": proc.stderr[-5000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "success": False,
            "exit_code": None,
            "stdout": (exc.stdout or "")[-5000:] if isinstance(exc.stdout, str) else "",
            "stderr": "timeout",
        }


def run() -> Dict[str, Any]:
    gui_probe = _probe(GUI)
    summary_probe = _probe(f"{BACKEND}/oracle/dashboard/summary")
    latest_before_body = _get_json("/oracle/dashboard/latest-events") if summary_probe["success"] else {"events": []}
    before = {str(event.get("oracle_trace_id")) for event in latest_before_body.get("events", []) if event.get("oracle_trace_id")}

    replay = _run_script(sys.executable, str(ROOT / "scripts" / "oracle_realtime_replay_proof.py"), "--events", "10", timeout=300)
    time.sleep(1)
    latest_after_body = _get_json("/oracle/dashboard/latest-events") if summary_probe["success"] else {"events": []}
    after = {str(event.get("oracle_trace_id")) for event in latest_after_body.get("events", []) if event.get("oracle_trace_id")}
    new_trace_ids = sorted(after - before)
    live_replay_events = [
        event
        for event in latest_after_body.get("events", [])
        if "LIVE_REPLAY" in str(event.get("data_source", ""))
    ]
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    build = _run_script(npm_cmd, "run", "build", timeout=600, cwd=GUI_DIR)

    gates = {
        "gui_reachable": gui_probe["success"],
        "backend_summary": summary_probe["success"],
        "latest_events_reachable": isinstance(latest_after_body.get("events"), list),
        "replay_success": replay["success"],
        "new_trace_ids_or_live_replay": bool(new_trace_ids) or bool(live_replay_events),
        "gui_build": build["success"],
    }
    report = {
        "generated_at": time.time(),
        "gui_url": GUI,
        "backend_url": BACKEND,
        "gates": gates,
        "gui_probe": gui_probe,
        "summary_probe": summary_probe,
        "latest_events_before": len(latest_before_body.get("events", [])),
        "latest_events_after": len(latest_after_body.get("events", [])),
        "new_trace_ids": new_trace_ids[:20],
        "live_replay_event_count": len(live_replay_events),
        "replay": replay,
        "gui_build": build,
        "browser_automation": "not_run; endpoint/build validation completed",
        "pass": all(gates.values()),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE GUI OPERATOR CONSOLE LIVE TEST ===")
    for name, ok in report["gates"].items():
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
    print(f"Latest events before: {report['latest_events_before']}")
    print(f"Latest events after: {report['latest_events_after']}")
    print(f"New trace IDs observed: {len(report['new_trace_ids'])}")
    print(f"LIVE_REPLAY events visible: {report['live_replay_event_count']}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
