"""Validate live GUI/dashboard status expectations for Phase 12.5B."""
from __future__ import annotations

import argparse
import hashlib
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parents[0]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from oracle_stack_common import (  # noqa: E402
    GUI_VALIDATION_DIR,
    check_health,
    kill_all_ports,
    start_gui_preview,
    start_services,
    wait_for_health,
)

REPORT_PATH = GUI_VALIDATION_DIR / "gui_live_status_report.json"
MODELS_FINAL = ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "models_final"
API_BASE = "http://127.0.0.1:8000"


def _hash_models_final() -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    if not MODELS_FINAL.exists():
        return hashes
    for path in MODELS_FINAL.rglob("*"):
        if path.is_file():
            hashes[str(path.relative_to(MODELS_FINAL))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _shutdown(procs: List[Any]) -> None:
    for proc in procs:
        if proc.poll() is None:
            try:
                proc.send_signal(signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
    time.sleep(2)
    for proc in procs:
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass


def _json_get(url: str) -> Dict[str, Any]:
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    return r.json()


def _gui_alive(port: int) -> Dict[str, Any]:
    try:
        r = requests.get(f"http://127.0.0.1:{port}", timeout=5)
        return {"alive": r.status_code < 500, "status_code": r.status_code}
    except Exception as exc:
        return {"alive": False, "error": str(exc)}


def _wait_gui_alive(port: int, timeout_s: float = 45.0) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    last = {"alive": False, "error": "not_checked"}
    while time.time() < deadline:
        last = _gui_alive(port)
        if last.get("alive") is True:
            return last
        time.sleep(2)
    return last


def validate_gui_live_status(gui_port: int = 4173, start_stack: bool = False) -> Dict[str, Any]:
    GUI_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    hashes_before = _hash_models_final()
    procs: List[Any] = []
    if start_stack:
        kill_all_ports()
        procs = start_services()
        wait_for_health(max_wait_s=120.0)
        gui = start_gui_preview(port=gui_port)
        if gui:
            procs.append(gui)
        time.sleep(5)
    try:
        health = check_health(timeout=3.0)
        summary = _json_get(f"{API_BASE}/oracle/dashboard/summary")
        evolution = _json_get(f"{API_BASE}/oracle/dashboard/evolution")
        arch = summary.get("architecture_status") or {}
        gui_status = _wait_gui_alive(gui_port) if start_stack else _gui_alive(gui_port)
        expected = {
            "Backend READY": summary.get("backend_status") == "READY" and arch.get("backend_ready") is True,
            "Async Assurance ON": arch.get("async_quantum_assurance_active") is True,
            "GhostTunnel ON": arch.get("ghosttunnel_fast_ack_active") is True,
            "Evolution READY": (arch.get("evolution_ready") is True or arch.get("evolution_dry_run_pass") is True),
            "Promotion BLOCKED_SAFE": arch.get("promotion_blocked_safe") is True,
        }
        not_expected = {
            "Backend UNKNOWN": summary.get("backend_status") == "UNKNOWN",
            "Evolution FAIL": not (arch.get("evolution_ready") is True or arch.get("evolution_dry_run_pass") is True),
            "Promotion UNSAFE": arch.get("promotion_blocked_safe") is not True,
        }
        hashes_after = _hash_models_final()
        report = {
            "generated_at": time.time(),
            "api_base": API_BASE,
            "gui_url": f"http://127.0.0.1:{gui_port}",
            "gui_alive": gui_status,
            "service_health": health,
            "dashboard_summary_backend_status": summary.get("backend_status"),
            "architecture_status": arch,
            "evolution_final_status": (evolution.get("evolution") or {}).get("final_status"),
            "expected_statuses": expected,
            "forbidden_statuses_present": not_expected,
            "pass": gui_status.get("alive") is True and all(health.values()) and all(expected.values()) and not any(not_expected.values()),
            "models_final_unchanged": hashes_before == hashes_after and len(hashes_before) > 0,
        }
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    finally:
        if start_stack:
            _shutdown(procs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate live GUI status")
    parser.add_argument("--gui-port", type=int, default=4173)
    parser.add_argument("--manage-stack", action="store_true", help="Start and stop a temporary validation stack.")
    parser.add_argument("--no-start-stack", action="store_true", help="Deprecated; operator mode is now the default.")
    args = parser.parse_args()
    report = validate_gui_live_status(args.gui_port, args.manage_stack and not args.no_start_stack)
    print("\n=== ORACLE GUI LIVE STATUS VALIDATION ===")
    for label, ok in report["expected_statuses"].items():
        print(f"{label}: {'PASS' if ok else 'FAIL'}")
    print(f"GUI reachable: {report['gui_alive'].get('alive')}")
    print(f"GUI Live Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print(f"Report: {REPORT_PATH}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
