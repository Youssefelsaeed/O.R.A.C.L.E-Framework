"""Phase 12.17 live replay and latest-events GUI update proof."""
from __future__ import annotations

import time
from typing import Any, Dict, Set

from oracle_phase12_17_common import CORE, ROOT, run_python_script, timed_request, write_report


def _latest() -> Dict[str, Any]:
    response = timed_request("GET", f"{CORE}/oracle/dashboard/latest-events", timeout=20)
    try:
        import requests

        body = requests.get(f"{CORE}/oracle/dashboard/latest-events", timeout=20).json()
    except Exception:
        body = {}
    response["events"] = body.get("events", []) if isinstance(body, dict) else []
    return response


def _trace_ids(events: list[Dict[str, Any]]) -> Set[str]:
    return {str(event.get("oracle_trace_id")) for event in events if event.get("oracle_trace_id")}


def run() -> Dict[str, Any]:
    before = _latest()
    before_ids = _trace_ids(before.get("events", []))
    replay = run_python_script("oracle_realtime_replay_proof.py", "--events", "50", timeout=300)
    after = _latest()
    after_events = after.get("events", [])
    after_ids = _trace_ids(after_events)
    new_ids = sorted(after_ids - before_ids)
    recent_cutoff = time.time() - 300
    live_replay_events = [event for event in after_events if "LIVE_REPLAY" in str(event.get("data_source", ""))]
    report = {
        "generated_at": time.time(),
        "before_event_count": len(before.get("events", [])),
        "after_event_count": len(after_events),
        "replay": replay,
        "new_trace_ids_count": len(new_ids),
        "new_trace_ids_sample": new_ids[:10],
        "live_replay_visible": bool(live_replay_events),
        "audit_logged_true": all(bool(event.get("audit_logged")) for event in live_replay_events[:20]) if live_replay_events else False,
        "recent_timestamps": all(float(event.get("timestamp", 0) or 0) >= recent_cutoff for event in live_replay_events[:20]) if live_replay_events else False,
        "gui_widget_source_present": "Latest ORACLE Events" in (ROOT / "O.R.A.C.L.E_GUi_V1_Figma" / "src" / "app" / "components" / "global-dashboard.tsx").read_text(encoding="utf-8", errors="ignore"),
        "dashboard_api_success": bool(after.get("success")),
    }
    report["pass"] = bool(
        replay.get("success")
        and report["new_trace_ids_count"] > 0
        and report["live_replay_visible"]
        and report["audit_logged_true"]
        and report["recent_timestamps"]
        and report["gui_widget_source_present"]
        and report["dashboard_api_success"]
    )
    path = write_report("phase12_17_live_replay_gui_update_test.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.17 LIVE REPLAY GUI UPDATE TEST ===")
    print(f"Replay Proof: {'PASS' if report['replay'].get('success') else 'FAIL'}")
    print(f"New Trace IDs: {report['new_trace_ids_count']}")
    print(f"LIVE_REPLAY Visible: {'PASS' if report['live_replay_visible'] else 'FAIL'}")
    print(f"Audit Logged True: {'PASS' if report['audit_logged_true'] else 'FAIL'}")
    print(f"Recent Timestamps: {'PASS' if report['recent_timestamps'] else 'FAIL'}")
    print(f"GUI Widget Source Present: {'PASS' if report['gui_widget_source_present'] else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
