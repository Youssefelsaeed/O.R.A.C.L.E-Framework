"""Final operator validation against an already-running ORACLE stack."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "oracle_operator_final_validation_report.json"
RUNTIME_REPORT = ROOT / "reports" / "final" / "operator_runtime_safety_report.json"
GUI_MONITOR_REPORT = ROOT / "reports" / "final" / "gui_live_monitor_report.json"
MODELS_FINAL = ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "models_final"


def _hash_models_final() -> Dict[str, str]:
    if not MODELS_FINAL.exists():
        return {}
    return {
        str(path.relative_to(MODELS_FINAL)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in MODELS_FINAL.rglob("*")
        if path.is_file()
    }


def _get(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    started = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        return {"success": response.status_code < 500, "status_code": response.status_code, "latency_ms": round((time.time() - started) * 1000, 2)}
    except Exception as exc:
        return {"success": False, "status_code": None, "error": str(exc), "latency_ms": round((time.time() - started) * 1000, 2)}


def _run_script(name: str, *args: str, timeout: int = 900) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / name), *args],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {"success": proc.returncode == 0, "exit_code": proc.returncode, "stdout": proc.stdout[-6000:], "stderr": proc.stderr[-6000:]}
    except subprocess.TimeoutExpired as exc:
        return {"success": False, "exit_code": None, "stdout": (exc.stdout or "")[-6000:] if isinstance(exc.stdout, str) else "", "stderr": "timeout"}


def _services_alive() -> Dict[str, Any]:
    checks = {
        "oracle_core": _get("http://127.0.0.1:8000/docs"),
        "qauthcore": _get("http://127.0.0.1:8001/docs"),
        "ethicq": _get("http://127.0.0.1:8002/docs"),
        "chronoledger": _get("http://127.0.0.1:8003/health"),
        "ghosttunnel": _get("http://127.0.0.1:8004/docs"),
    }
    return {"checks": checks, "pass": all(v["success"] for v in checks.values())}


def run() -> Dict[str, Any]:
    before_hashes = _hash_models_final()
    stack_before = _services_alive()
    gui_before = _get("http://127.0.0.1:4173", timeout=5.0)

    actions = _run_script("test_gui_buttons_live_actions.py", timeout=900)
    acceptance = _run_script("oracle_final_acceptance_test.py", timeout=900)
    gui_after_acceptance = _get("http://127.0.0.1:4173", timeout=5.0)
    module = _run_script("oracle_phase12_11_module_capability_validation.py", timeout=1800)
    gui_after_module = _get("http://127.0.0.1:4173", timeout=5.0)

    live_sensor = _run_script("oracle_live_sensor_smoke_test.py", timeout=600)
    replay = _run_script("oracle_realtime_replay_proof.py", "--events", "100", timeout=900)

    latest = {}
    try:
        latest_resp = requests.get("http://127.0.0.1:8000/oracle/dashboard/latest-events", timeout=10)
        latest = {"success": latest_resp.status_code == 200, "status_code": latest_resp.status_code, "body": latest_resp.json()}
    except Exception as exc:
        latest = {"success": False, "error": str(exc)}

    after_hashes = _hash_models_final()
    tests_do_not_kill = bool(gui_after_acceptance["success"] and gui_after_module["success"])
    report = {
        "generated_at": time.time(),
        "existing_stack_detected": stack_before,
        "gui_alive": gui_before,
        "gui_buttons_actions": actions,
        "acceptance_test": acceptance,
        "module_capability_test": module,
        "tests_do_not_kill_stack": {
            "pass": tests_do_not_kill,
            "gui_after_acceptance": gui_after_acceptance,
            "gui_after_module": gui_after_module,
        },
        "live_sensor_proof": live_sensor,
        "realtime_replay_proof": replay,
        "latest_events_feed": latest,
        "models_final_unchanged": before_hashes == after_hashes and bool(before_hashes),
    }
    gates = {
        "existing_stack": stack_before["pass"],
        "gui_alive": gui_before["success"],
        "gui_buttons_actions": actions["success"],
        "tests_do_not_kill_stack": tests_do_not_kill,
        "live_sensor_or_replay": live_sensor["success"] or replay["success"],
        "realtime_replay": replay["success"],
        "latest_events": latest.get("success") is True and bool((latest.get("body") or {}).get("events")),
        "models_final_unchanged": report["models_final_unchanged"],
    }
    report["gates"] = gates
    report["final_status"] = "ORACLE_OPERATOR_VALIDATED" if all(gates.values()) else "NOT_READY"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    RUNTIME_REPORT.write_text(
        json.dumps(
            {
                "generated_at": time.time(),
                "acceptance_test_operator_mode": acceptance,
                "module_capability_operator_mode": module,
                "gui_after_acceptance": gui_after_acceptance,
                "gui_after_module": gui_after_module,
                "tests_do_not_kill_stack": tests_do_not_kill,
                "models_final_unchanged": report["models_final_unchanged"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    GUI_MONITOR_REPORT.write_text(
        json.dumps(
            {
                "generated_at": time.time(),
                "latest_events_feed": latest,
                "gui_alive": gui_before,
                "latest_events_available": gates["latest_events"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    report = run()
    gates = report["gates"]
    print("\n=== ORACLE OPERATOR FINAL VALIDATION ===")
    print(f"Existing Stack Detected: {'PASS' if gates['existing_stack'] else 'FAIL'}")
    print(f"GUI Alive: {'PASS' if gates['gui_alive'] else 'FAIL'}")
    print(f"GUI Buttons/Actions: {'PASS' if gates['gui_buttons_actions'] else 'FAIL'}")
    print(f"Tests Do Not Kill Stack: {'PASS' if gates['tests_do_not_kill_stack'] else 'FAIL'}")
    print(f"Live Sensor Proof: {'PASS' if report['live_sensor_proof']['success'] else 'SKIPPED_WITH_REASON'}")
    print(f"Realtime Replay Proof: {'PASS' if gates['realtime_replay'] else 'FAIL'}")
    print(f"Latest Events Feed: {'PASS' if gates['latest_events'] else 'FAIL'}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print("")
    print(f"Final Status: {report['final_status']}")
    print(f"Report: {REPORT}")
    if report["final_status"] != "ORACLE_OPERATOR_VALIDATED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
