"""
One-command launcher for Project O.R.A.C.L.E. service stack (+ optional GUI preview).

Usage:
  python scripts/start_oracle_stack.py
  python scripts/start_oracle_stack.py --gui
  python scripts/start_oracle_stack.py --kill-existing
"""
from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from oracle_stack_common import (
    SERVICE_LABELS,
    check_health,
    kill_all_ports,
    print_service_urls,
    start_gui_preview,
    start_services,
    wait_for_health,
)

PROCS: List = []
GUI_VALIDATION_DIR = Path(__file__).resolve().parents[1] / "reports" / "final" / "gui_validation"


def _tail(path: str | None, max_lines: int = 80) -> List[str]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except Exception as exc:
        return [f"<tail_read_error:{exc!s}>"]


def _extract_traceback(stderr_tail: List[str]) -> str | None:
    for idx, line in enumerate(stderr_tail):
        if "Traceback (most recent call last)" in line:
            return "\n".join(stderr_tail[idx:])
    return None


def _process_report(proc: Any) -> Dict[str, Any]:
    started_at = float(getattr(proc, "oracle_started_at", time.time()))
    stderr_tail = _tail(getattr(proc, "oracle_stderr_log", None))
    stdout_tail = _tail(getattr(proc, "oracle_stdout_log", None))
    traceback = _extract_traceback(stderr_tail)
    return {
        "service_name": getattr(proc, "oracle_service_name", "unknown"),
        "pid": proc.pid,
        "port": getattr(proc, "oracle_service_port", None),
        "exit_code": proc.poll(),
        "uptime_seconds": round(max(0.0, time.time() - started_at), 2),
        "stdout_log": getattr(proc, "oracle_stdout_log", None),
        "stderr_log": getattr(proc, "oracle_stderr_log", None),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "exception": stderr_tail[-1] if stderr_tail else None,
        "traceback": traceback,
    }


def _write_exit_report(dead_proc: Any) -> Dict[str, Any]:
    GUI_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": time.time(),
        "service_name": getattr(dead_proc, "oracle_service_name", "unknown"),
        "pid": dead_proc.pid,
        "exit_code": dead_proc.poll(),
        "uptime_seconds": round(max(0.0, time.time() - float(getattr(dead_proc, "oracle_started_at", time.time()))), 2),
        "dead_process": _process_report(dead_proc),
        "all_processes": [_process_report(p) for p in PROCS],
    }
    path = GUI_VALIDATION_DIR / "service_exit_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _shutdown(*_args) -> None:
    print("\nShutting down ORACLE stack...")
    for proc in PROCS:
        try:
            proc.terminate()
        except Exception:
            pass
    time.sleep(1)
    for proc in PROCS:
        try:
            proc.kill()
        except Exception:
            pass
    sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Start ORACLE backend stack")
    parser.add_argument("--gui", action="store_true", help="Also start GUI preview on port 4173")
    parser.add_argument("--kill-existing", action="store_true", help="Kill processes on ORACLE ports first")
    parser.add_argument("--gui-port", type=int, default=4173)
    args = parser.parse_args()

    if args.kill_existing:
        print("Stopping existing processes on ORACLE ports...")
        kill_all_ports()

    print("Starting ORACLE services...")
    PROCS.extend(start_services())

    print("Waiting for health checks...")
    health = wait_for_health(max_wait_s=120.0)
    print("\n=== STARTUP HEALTH ===")
    all_ok = True
    for name, ok in health.items():
        status = "UP" if ok else "DOWN"
        print(f"  {SERVICE_LABELS.get(name, name):16} {status}")
        if not ok:
            all_ok = False

    if args.gui:
        gui_proc = start_gui_preview(port=args.gui_port)
        if gui_proc:
            PROCS.append(gui_proc)
            print(f"\nGUI preview starting on http://127.0.0.1:{args.gui_port}")

    print_service_urls(include_gui=args.gui, gui_port=args.gui_port)

    if not all_ok:
        print("WARNING: Some services did not pass health check. Check logs and ports.")
    else:
        print("All services healthy. Press Ctrl+C to stop.\n")

    signal.signal(signal.SIGINT, _shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            time.sleep(5)
            dead = [p for p in PROCS if p.poll() is not None]
            if dead:
                report = _write_exit_report(dead[0])
                print(
                    "A service process exited unexpectedly: "
                    f"{report['service_name']} pid={report['pid']} "
                    f"exit_code={report['exit_code']} uptime={report['uptime_seconds']}s"
                )
                print(f"Service exit report: {GUI_VALIDATION_DIR / 'service_exit_report.json'}")
                _shutdown()
    except KeyboardInterrupt:
        _shutdown()


if __name__ == "__main__":
    main()
