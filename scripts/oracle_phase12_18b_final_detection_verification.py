"""Run Phase 12.18B final controlled detection verification."""
from __future__ import annotations

import subprocess
import sys
import time
from typing import Any, Dict

from oracle_phase12_17_common import model_hashes
from oracle_phase12_18_common import ROOT, write_json

STEPS = {
    "Runtime Current Code": ("oracle_phase12_18b_hard_runtime_reset.py", 360),
    "Balanced Eval Sets": ("oracle_phase12_18b_build_balanced_eval_sets.py", 360),
    "Detector Routing Audit": ("oracle_phase12_18b_detector_routing_audit.py", 240),
    "Standalone MutantShield Eval": ("oracle_phase12_18b_mutantshield_controlled_eval.py", 1200),
    "Full Stack Oracle Eval": ("oracle_phase12_18b_full_stack_controlled_eval.py", 1800),
    "Original Metrics Comparison": ("oracle_phase12_18b_compare_original_mutantshield_metrics.py", 240),
    "Final Detection Verdict": ("oracle_phase12_18b_final_detection_verdict.py", 240),
    "Request Handling Recheck": ("oracle_phase12_18b_request_handling_final_rerun.py", 1200),
    "GitHub Safety": ("github_release_safety_check.py", 240),
}


def _run(script: str, timeout: int) -> Dict[str, Any]:
    started = time.time()
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return {"script": script, "exit_code": proc.returncode, "success": proc.returncode == 0, "duration_seconds": round(time.time() - started, 2), "stdout_tail": proc.stdout[-5000:], "stderr_tail": proc.stderr[-2500:]}


def run() -> Dict[str, Any]:
    before = model_hashes()
    steps = {name: _run(script, timeout) for name, (script, timeout) in STEPS.items()}
    after = model_hashes()
    report: Dict[str, Any] = {"generated_at": time.time(), "steps": steps, "models_final_unchanged": bool(before) and before == after}
    report["pass"] = all(s["success"] for s in steps.values()) and report["models_final_unchanged"]
    report["final_status"] = "ORACLE_DETECTION_VERIFIED" if report["pass"] else "NOT_READY"
    path = write_json("phase12_18b_final_detection_verification.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B FINAL DETECTION VERIFICATION ===")
    for name in STEPS:
        print(f"{name}: {'PASS' if report['steps'][name]['success'] else 'FAIL'}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print("\nFinal Status:")
    print(report["final_status"])
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        print("\nFailed step details:")
        for name, step in report["steps"].items():
            if not step["success"]:
                print(f"\n--- {name} stdout ---")
                print(step.get("stdout_tail", ""))
                print(f"--- {name} stderr ---")
                print(step.get("stderr_tail", ""))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
