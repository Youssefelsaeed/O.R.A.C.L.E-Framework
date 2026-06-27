"""Phase 12.18 clean runtime reset and stale listener audit."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

from oracle_phase12_18_common import CORE, GUI, ROOT, git_commit, write_json

PORTS = [8000, 8001, 8002, 8003, 8004, 4173]


def _listeners() -> List[Dict[str, Any]]:
    ps = (
        "Get-NetTCPConnection -State Listen -LocalPort "
        + ",".join(str(p) for p in PORTS)
        + " | Select-Object LocalPort,OwningProcess | ConvertTo-Json"
    )
    try:
        raw = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, errors="replace", timeout=20)
        data = json.loads(raw) if raw.strip() else []
        if isinstance(data, dict):
            data = [data]
    except Exception:
        data = []
    out: List[Dict[str, Any]] = []
    for item in data:
        pid = int(item.get("OwningProcess") or 0)
        detail = _process_detail(pid)
        out.append({"port": int(item.get("LocalPort") or 0), "pid": pid, **detail})
    return out


def _process_detail(pid: int) -> Dict[str, Any]:
    if pid <= 0:
        return {"process_name": None, "command_line": None, "oracle_owned": False, "resolvable": False}
    ps = (
        f"Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\" "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json"
    )
    try:
        raw = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps], text=True, errors="replace", timeout=20)
        if not raw.strip():
            return {"process_name": None, "command_line": None, "oracle_owned": False, "resolvable": False}
        data = json.loads(raw)
        cmd = str(data.get("CommandLine") or "")
        name = str(data.get("Name") or "")
        root_markers = [str(ROOT).lower(), "oracle_core", "qauthcore", "ethicq", "chronoledger", "ghosttunnel", "vite"]
        oracle_owned = any(marker in cmd.lower() for marker in root_markers)
        return {"process_name": name, "command_line": cmd, "oracle_owned": oracle_owned, "resolvable": True}
    except Exception as exc:
        return {"process_name": None, "command_line": None, "oracle_owned": False, "resolvable": False, "detail_error": str(exc)}


def _kill_oracle_owned(listeners: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    killed: List[Dict[str, Any]] = []
    for item in listeners:
        if not item.get("oracle_owned"):
            continue
        pid = int(item.get("pid") or 0)
        result = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], text=True, capture_output=True, timeout=30)
        killed.append({**item, "taskkill_exit_code": result.returncode, "taskkill_stdout": result.stdout[-1000:], "taskkill_stderr": result.stderr[-1000:]})
    return killed


def _start_stack() -> Dict[str, Any]:
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "start_oracle_stack.py"), "--gui", "--kill-existing"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.time() + 180
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        last = _health_snapshot()
        if all(v.get("ok") for v in last.values()):
            break
        time.sleep(3)
    return {"pid": proc.pid, "poll": proc.poll(), "health": last, "started": all(v.get("ok") for v in last.values())}


def _health_snapshot() -> Dict[str, Any]:
    checks = {
        "oracle_core": f"{CORE}/health",
        "qauthcore": "http://127.0.0.1:8001/docs",
        "ethicq": "http://127.0.0.1:8002/docs",
        "chronoledger": "http://127.0.0.1:8003/health",
        "ghosttunnel": "http://127.0.0.1:8004/docs",
        "gui": GUI,
    }
    out: Dict[str, Any] = {}
    for name, url in checks.items():
        try:
            r = requests.get(url, timeout=5)
            body: Any
            try:
                body = r.json()
            except Exception:
                body = {"text": r.text[:100]}
            out[name] = {"ok": r.status_code < 400, "status_code": r.status_code, "body": body}
        except Exception as exc:
            out[name] = {"ok": False, "error": str(exc)}
    return out


def _current_code_verified() -> Dict[str, Any]:
    expected_commit = git_commit()
    result: Dict[str, Any] = {"expected_git_commit": expected_commit}
    try:
        health = requests.get(f"{CORE}/health", timeout=10).json()
    except Exception as exc:
        health = {"error": str(exc)}
    try:
        summary = requests.get(f"{CORE}/oracle/dashboard/summary", timeout=10).json()
    except Exception as exc:
        summary = {"error": str(exc)}
    try:
        gui = requests.get(GUI, timeout=10)
        gui_ok = gui.status_code < 400
    except Exception:
        gui_ok = False
    runtime = summary.get("runtime") if isinstance(summary, dict) else {}
    result.update(
        {
            "health": health,
            "summary_runtime": runtime,
            "gui_reachable": gui_ok,
            "health_has_phase12_18_field": "token_cache_ttl_seconds" in health,
            "summary_has_runtime_marker": (runtime or {}).get("code_marker") == "phase12_18_runtime_metadata",
            "summary_git_commit_matches": bool(expected_commit) and (runtime or {}).get("git_commit") == expected_commit,
        }
    )
    result["verified"] = bool(result["health_has_phase12_18_field"] and result["summary_has_runtime_marker"] and result["summary_git_commit_matches"] and gui_ok)
    return result


def run() -> Dict[str, Any]:
    before = _listeners()
    killed = _kill_oracle_owned(before)
    time.sleep(2)
    after_kill = _listeners()
    start = _start_stack()
    verification = _current_code_verified()
    after_start = _listeners()
    report = {
        "generated_at": time.time(),
        "ports": PORTS,
        "listeners_before": before,
        "stale_processes_removed": killed,
        "listeners_after_kill": after_kill,
        "stack_restart": start,
        "current_code": verification,
        "listeners_after_start": after_start,
    }
    report["ports_checked"] = True
    report["stack_restarted"] = bool(start.get("started"))
    report["current_code_verified"] = bool(verification.get("verified"))
    report["pass"] = report["ports_checked"] and report["stack_restarted"] and report["current_code_verified"]
    path = write_json("phase12_18_clean_runtime_reset.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18 CLEAN RUNTIME RESET ===")
    print(f"Ports Checked: {'PASS' if report['ports_checked'] else 'FAIL'}")
    print(f"Stale Processes Removed: {len(report['stale_processes_removed'])}")
    print(f"Stack Restarted: {'PASS' if report['stack_restarted'] else 'FAIL'}")
    print(f"Current Code Verified: {'PASS' if report['current_code_verified'] else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
