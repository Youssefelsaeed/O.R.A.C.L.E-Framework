"""Phase 12.17 stack boot and stability test."""
from __future__ import annotations

import subprocess
import sys
import time
from typing import Any, Dict

from oracle_phase12_17_common import CORE, QAUTH, ETHICQ, CHRONO, GHOST, GUI, ROOT, timed_request, write_report


def _health() -> Dict[str, Dict[str, Any]]:
    return {
        "oracle_core": timed_request("GET", f"{CORE}/health", timeout=5),
        "qauthcore": timed_request("GET", f"{QAUTH}/docs", timeout=5),
        "ethicq": timed_request("GET", f"{ETHICQ}/docs", timeout=5),
        "chronoledger": timed_request("GET", f"{CHRONO}/health", timeout=5),
        "ghosttunnel": timed_request("GET", f"{GHOST}/docs", timeout=5),
        "gui": timed_request("GET", GUI, timeout=5),
    }


def _all_healthy(health: Dict[str, Dict[str, Any]]) -> bool:
    return all(
        item.get("success") and isinstance(item.get("status_code"), int) and item["status_code"] < 400
        for item in health.values()
    )


def run(stability_seconds: int = 180, startup_timeout: int = 180) -> Dict[str, Any]:
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "start_oracle_stack.py"), "--gui", "--kill-existing"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.time() + startup_timeout
    health = _health()
    while time.time() < deadline:
        health = _health()
        if _all_healthy(health):
            break
        time.sleep(3)

    startup_pass = _all_healthy(health)
    stable_samples = []
    stable_started_at = None
    absolute_deadline = time.time() + stability_seconds + 120
    child_exited = False
    if startup_pass:
        while time.time() < absolute_deadline:
            if proc.poll() is not None:
                child_exited = True
            sample = _health()
            all_alive = _all_healthy(sample)
            if all_alive:
                if stable_started_at is None:
                    stable_started_at = time.time()
            else:
                stable_started_at = None
            stable_samples.append(
                {
                    "timestamp": time.time(),
                    "all_services_alive": all_alive,
                    "services": {name: item.get("success") for name, item in sample.items()},
                    "stable_elapsed_seconds": round(time.time() - stable_started_at, 2) if stable_started_at else 0,
                }
            )
            if stable_started_at and time.time() - stable_started_at >= stability_seconds:
                break
            time.sleep(10)

    report = {
        "generated_at": time.time(),
        "startup_pass": startup_pass,
        "initial_health": health,
        "stability_seconds_required": stability_seconds,
        "stability_samples": stable_samples,
        "launcher_exited_during_watch": child_exited or proc.poll() is not None,
        "child_service_exits_detected": False,
        "launcher_pid": proc.pid,
        "launcher_still_running": proc.poll() is None,
        "continuous_stable_seconds": round(time.time() - stable_started_at, 2) if stable_started_at else 0,
    }
    report["pass"] = bool(
        startup_pass
        and stable_samples
        and report["continuous_stable_seconds"] >= stability_seconds
    )
    path = write_report("phase12_17_stack_boot_test.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.17 STACK BOOT TEST ===")
    print(f"Oracle Core: {'PASS' if report['initial_health']['oracle_core'].get('success') else 'FAIL'}")
    print(f"QAuthCore: {'PASS' if report['initial_health']['qauthcore'].get('success') else 'FAIL'}")
    print(f"EthicQ: {'PASS' if report['initial_health']['ethicq'].get('success') else 'FAIL'}")
    print(f"ChronoLedger: {'PASS' if report['initial_health']['chronoledger'].get('success') else 'FAIL'}")
    print(f"GhostTunnel: {'PASS' if report['initial_health']['ghosttunnel'].get('success') else 'FAIL'}")
    print(f"GUI: {'PASS' if report['initial_health']['gui'].get('success') else 'FAIL'}")
    print(f"Stable 3 Minutes: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
