"""Run the full Phase 12.17 final operational verification loop."""
from __future__ import annotations

import json
import time
from typing import Any, Dict

from oracle_phase12_17_common import model_hashes, run_python_script, write_report


def _run(label: str, script: str, timeout: int) -> Dict[str, Any]:
    result = run_python_script(script, timeout=timeout)
    return {"label": label, "script": script, **result}


def run() -> Dict[str, Any]:
    before_hashes = model_hashes()
    steps = {
        "Stack Boot": _run("Stack Boot", "oracle_phase12_17_stack_boot_test.py", 420),
        "Backend Endpoints": _run("Backend Endpoints", "oracle_phase12_17_backend_endpoint_test.py", 600),
        "GUI Actions": _run("GUI Actions", "oracle_phase12_17_gui_action_test.py", 600),
        "Request Handling": _run("Request Handling", "oracle_phase12_17_request_handling_test.py", 1200),
        "Live Replay GUI Update": _run("Live Replay GUI Update", "oracle_phase12_17_live_replay_gui_update_test.py", 420),
        "Reports & Docs": _run("Reports & Docs", "oracle_phase12_17_reports_docs_test.py", 180),
        "Issue Sweep": _run("Issue Sweep", "oracle_phase12_17_issue_sweep.py", 180),
        "GitHub Safety": _run("GitHub Safety", "github_release_safety_check.py", 240),
        "Final Acceptance": _run("Final Acceptance", "oracle_final_acceptance_test.py", 1800),
    }
    after_hashes = model_hashes()
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "steps": steps,
        "models_final_unchanged": bool(before_hashes) and before_hashes == after_hashes,
    }
    report["pass"] = all(step.get("success") for step in steps.values()) and report["models_final_unchanged"]
    report["final_status"] = "ORACLE_FINAL_OPERATIONALLY_VERIFIED" if report["pass"] else "NOT_READY"
    path = write_report("phase12_17_final_operational_verification.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.17 FINAL OPERATIONAL VERIFICATION ===")
    for label in [
        "Stack Boot",
        "Backend Endpoints",
        "GUI Actions",
        "Request Handling",
        "Live Replay GUI Update",
        "Reports & Docs",
        "Issue Sweep",
        "GitHub Safety",
        "Final Acceptance",
    ]:
        print(f"{label}: {'PASS' if report['steps'][label].get('success') else 'FAIL'}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print("\nFinal Status:")
    print(report["final_status"])
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        print("\nFailed step details:")
        for label, step in report["steps"].items():
            if not step.get("success"):
                print(f"\n--- {label} stdout ---")
                print(step.get("stdout_tail", ""))
                print(f"--- {label} stderr ---")
                print(step.get("stderr_tail", ""))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
