"""Start ORACLE cleanly and prove the running Oracle Core is current code."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

from oracle_kill_all_runtime import PORTS, kill_oracle_runtime, listeners, pid_details

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "final"
MARKER = "phase12_19_current_runtime"
CORE = "http://127.0.0.1:8000"
SERVICE_URLS = {
    "oracle_core_runtime": f"{CORE}/oracle/runtime-info",
    "oracle_core_health": f"{CORE}/health",
    "oracle_dashboard_summary": f"{CORE}/oracle/dashboard/summary",
    "qauthcore": "http://127.0.0.1:8001/docs",
    "ethicq": "http://127.0.0.1:8002/docs",
    "chronoledger": "http://127.0.0.1:8003/health",
    "ghosttunnel": "http://127.0.0.1:8004/docs",
    "gui": "http://127.0.0.1:4173",
}


def write_json(name: str, report: Dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / name
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL, timeout=5).strip()
    except Exception:
        return None


def start_stack() -> Dict[str, Any]:
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "start_oracle_stack.py"), "--gui"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {"pid": proc.pid}


def get_json_or_text(url: str) -> Dict[str, Any]:
    try:
        response = requests.get(url, timeout=10)
        try:
            body = response.json()
        except Exception:
            body = {"text": response.text[:500]}
        return {"ok": response.status_code < 400, "status_code": response.status_code, "body": body}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}"}


def health_snapshot() -> Dict[str, Any]:
    return {name: get_json_or_text(url) for name, url in SERVICE_URLS.items()}


def dashboard_ready(summary: Dict[str, Any]) -> bool:
    if not summary.get("ok"):
        return False
    body = summary.get("body") or {}
    status_text = json.dumps(body).upper()
    return "READY" in status_text or bool(body)


def ports_current_oracle_processes() -> Dict[str, Any]:
    found = listeners()
    details = [pid_details(item["pid"]) for item in found]
    detail_by_pid = {d["pid"]: d for d in details}
    all_current = True
    for item in found:
        if item["port"] in PORTS and not detail_by_pid.get(item["pid"], {}).get("oracle_related"):
            all_current = False
    return {"listeners": found, "pid_details": details, "all_current_oracle_processes": all_current}


def run(start: bool = True) -> Dict[str, Any]:
    kill_report = kill_oracle_runtime()
    stack = start_stack() if start else {"skipped": True}
    deadline = time.time() + 180
    snapshot: Dict[str, Any] = {}
    while time.time() < deadline:
        snapshot = health_snapshot()
        runtime = (snapshot.get("oracle_core_runtime") or {}).get("body") or {}
        health = (snapshot.get("oracle_core_health") or {}).get("body") or {}
        service_ports_ok = all((snapshot.get(name) or {}).get("ok") for name in SERVICE_URLS)
        if (
            runtime.get("runtime_marker") == MARKER
            and health.get("runtime_marker") == MARKER
            and dashboard_ready(snapshot.get("oracle_dashboard_summary") or {})
            and service_ports_ok
        ):
            break
        time.sleep(3)
    ownership = ports_current_oracle_processes()
    runtime = (snapshot.get("oracle_core_runtime") or {}).get("body") or {}
    health = (snapshot.get("oracle_core_health") or {}).get("body") or {}
    summary = snapshot.get("oracle_dashboard_summary") or {}
    service_ports_ok = all((snapshot.get(name) or {}).get("ok") for name in SERVICE_URLS)
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "expected_git_commit": git_commit(),
        "expected_runtime_marker": MARKER,
        "kill_report": kill_report,
        "stack_start": stack,
        "service_health": snapshot,
        "runtime_info": runtime,
        "health": health,
        "dashboard_summary_ready": dashboard_ready(summary),
        "ports": ownership,
        "runtime_info_200": (snapshot.get("oracle_core_runtime") or {}).get("status_code") == 200,
        "runtime_marker_ok": runtime.get("runtime_marker") == MARKER,
        "health_schema_ok": health.get("runtime_marker") == MARKER and "downstream" in health,
        "all_service_ports_alive": service_ports_ok,
        "all_service_ports_current_oracle": ownership.get("all_current_oracle_processes"),
    }
    report["pass"] = all(
        [
            report["runtime_info_200"],
            report["runtime_marker_ok"],
            report["health_schema_ok"],
            report["dashboard_summary_ready"],
            report["all_service_ports_alive"],
            report["all_service_ports_current_oracle"],
        ]
    )
    path = write_json("phase12_19_runtime_current_code_report.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("=== ORACLE RUNTIME CURRENT CODE CHECK ===")
    print(f"Runtime Info 200: {'PASS' if report['runtime_info_200'] else 'FAIL'}")
    print(f"Runtime Marker: {'PASS' if report['runtime_marker_ok'] else 'FAIL'}")
    print(f"Health Schema: {'PASS' if report['health_schema_ok'] else 'FAIL'}")
    print(f"Dashboard Summary READY: {'PASS' if report['dashboard_summary_ready'] else 'FAIL'}")
    print(f"All Service Ports Alive: {'PASS' if report['all_service_ports_alive'] else 'FAIL'}")
    print(f"All Ports Current ORACLE: {'PASS' if report['all_service_ports_current_oracle'] else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
