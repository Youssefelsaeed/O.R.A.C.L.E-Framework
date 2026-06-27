"""Run Phase 12.18 clean runtime and detection truth audit."""
from __future__ import annotations

import subprocess
import sys
import time
from typing import Any, Dict

from oracle_phase12_17_common import model_hashes
from oracle_phase12_18_common import ROOT, write_json


STEPS = {
    "Clean Runtime Reset": ("oracle_phase12_18_clean_runtime_reset.py", 300),
    "Feature Mapping Audit": ("oracle_phase12_18_feature_mapping_audit.py", 300),
    "MutantShield Standalone Eval": ("oracle_phase12_18_mutantshield_standalone_eval.py", 900),
    "Full Stack Dataset Eval": ("oracle_phase12_18_full_stack_dataset_eval.py", 900),
    "Metric Truth Comparison": ("oracle_phase12_18_metric_truth_comparison.py", 180),
    "Request Handling Rerun": ("oracle_phase12_18_request_handling_rerun.py", 1200),
    "GitHub Safety": ("github_release_safety_check.py", 240),
}


def _run(script: str, timeout: int) -> Dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "script": script,
        "exit_code": proc.returncode,
        "success": proc.returncode == 0,
        "duration_seconds": round(time.time() - started, 2),
        "stdout_tail": proc.stdout[-5000:],
        "stderr_tail": proc.stderr[-2500:],
    }


def run() -> Dict[str, Any]:
    before = model_hashes()
    results = {name: _run(script, timeout) for name, (script, timeout) in STEPS.items()}
    after = model_hashes()
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "steps": results,
        "models_final_unchanged": bool(before) and before == after,
    }
    report["pass"] = all(step["success"] for step in results.values()) and report["models_final_unchanged"]
    report["final_status"] = "ORACLE_DETECTION_TRUTH_VERIFIED" if report["pass"] else "NOT_READY"
    path = write_json("phase12_18_detection_truth_audit.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18 DETECTION TRUTH AUDIT ===")
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
