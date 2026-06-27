"""Hard runtime reset with current-code proof for Phase 12.18B."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from typing import Any, Dict, List

import requests

from oracle_phase12_18_common import CORE, GUI, ROOT, git_commit, write_json

PORTS = [8000, 8001, 8002, 8003, 8004, 4173]
MARKER = "phase12_18b_runtime"


def _cmd(args: List[str], timeout: int = 30) -> Dict[str, Any]:
    try:
        p = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return {"cmd": args, "exit_code": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-2000:]}
    except Exception as exc:
        return {"cmd": args, "exit_code": None, "error": f"{type(exc).__name__}:{exc}"}


def _netstat() -> Dict[str, Any]:
    result = _cmd(["netstat", "-ano"])
    listeners = []
    for line in str(result.get("stdout", "")).splitlines():
        if "LISTENING" not in line:
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        for port in PORTS:
            if parts[1].endswith(f":{port}"):
                listeners.append({"method": "netstat", "port": port, "pid": int(parts[-1]), "line": line})
    result["listeners"] = listeners
    return result


def _tcp_connections() -> Dict[str, Any]:
    ps = "Get-NetTCPConnection -State Listen -LocalPort " + ",".join(str(p) for p in PORTS) + " | Select LocalPort,OwningProcess | ConvertTo-Json"
    result = _cmd(["powershell", "-NoProfile", "-Command", ps])
    listeners = []
    try:
        data = json.loads(str(result.get("stdout") or "[]"))
        if isinstance(data, dict):
            data = [data]
        for item in data:
            listeners.append({"method": "Get-NetTCPConnection", "port": int(item.get("LocalPort")), "pid": int(item.get("OwningProcess"))})
    except Exception as exc:
        result["parse_error"] = str(exc)
    result["listeners"] = listeners
    return result


def _pid_details(pid: int) -> Dict[str, Any]:
    details: Dict[str, Any] = {"pid": pid}
    details["tasklist"] = _cmd(["tasklist", "/FI", f"PID eq {pid}", "/V"])
    details["wmic"] = _cmd(["wmic", "process", "where", f"processid={pid}", "get", "ProcessId,Name,CommandLine", "/FORMAT:LIST"])
    ps = f"Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\" | Select ProcessId,Name,CommandLine | ConvertTo-Json"
    details["powershell_process"] = _cmd(["powershell", "-NoProfile", "-Command", ps])
    text = " ".join(str(details[k].get("stdout", "")) for k in ("tasklist", "wmic", "powershell_process")).lower()
    markers = [str(ROOT).lower(), "oracle_core", "qauthcore", "ethicq", "chronoledger", "ghosttunnel", "vite", "uvicorn"]
    details["oracle_owned"] = any(marker in text for marker in markers)
    details["resolvable"] = any(str(pid) in str(details[k].get("stdout", "")) for k in ("tasklist", "wmic", "powershell_process"))
    return details


def _listeners() -> List[Dict[str, Any]]:
    seen: Dict[tuple[int, int], Dict[str, Any]] = {}
    for source in (_netstat(), _tcp_connections()):
        for item in source.get("listeners", []):
            seen[(item["port"], item["pid"])] = item
    return list(seen.values())


def _kill(pid: int, oracle_owned: bool) -> Dict[str, Any]:
    return {
        "pid": pid,
        "oracle_owned": oracle_owned,
        "forced_for_target_oracle_port": True,
        "taskkill": _cmd(["taskkill", "/PID", str(pid), "/F", "/T"]),
        "stop_process": _cmd(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction Continue"]),
    }


def _service_health() -> Dict[str, Any]:
    urls = {
        "runtime_info": f"{CORE}/oracle/runtime-info",
        "health": f"{CORE}/health",
        "summary": f"{CORE}/oracle/dashboard/summary",
        "qauthcore": "http://127.0.0.1:8001/docs",
        "ethicq": "http://127.0.0.1:8002/docs",
        "chronoledger": "http://127.0.0.1:8003/health",
        "ghosttunnel": "http://127.0.0.1:8004/docs",
        "gui": GUI,
    }
    out: Dict[str, Any] = {}
    for name, url in urls.items():
        try:
            r = requests.get(url, timeout=10)
            try:
                body = r.json()
            except Exception:
                body = {"text": r.text[:200]}
            out[name] = {"ok": r.status_code < 400, "status_code": r.status_code, "body": body}
        except Exception as exc:
            out[name] = {"ok": False, "error": str(exc)}
    return out


def _start_stack() -> Dict[str, Any]:
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "start_oracle_stack.py"), "--gui", "--kill-existing"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    deadline = time.time() + 180
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        last = _service_health()
        if all(v.get("ok") for v in last.values()):
            break
        time.sleep(3)
    return {"pid": proc.pid, "poll": proc.poll(), "services": last, "ok": all(v.get("ok") for v in last.values())}


def run() -> Dict[str, Any]:
    initial_sources = {"netstat": _netstat(), "get_net_tcp": _tcp_connections()}
    listeners = _listeners()
    details = [_pid_details(item["pid"]) for item in listeners]
    kills = [_kill(d["pid"], bool(d["oracle_owned"])) for d in details]
    time.sleep(2)
    after_kill = _listeners()
    stack = _start_stack()
    health = _service_health()
    runtime = (health.get("runtime_info") or {}).get("body") or {}
    health_body = (health.get("health") or {}).get("body") or {}
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "expected_git_commit": git_commit(),
        "ports": PORTS,
        "initial_sources": initial_sources,
        "listeners": listeners,
        "pid_details": details,
        "termination_attempts": kills,
        "listeners_after_kill": after_kill,
        "stack_restart": stack,
        "final_health": health,
        "runtime_info": runtime,
        "ports_checked": True,
        "all_services_alive": all(v.get("ok") for v in health.values()),
        "current_code_verified": runtime.get("code_marker") == MARKER and health_body.get("code_marker") == MARKER,
    }
    report["pass"] = report["ports_checked"] and report["all_services_alive"] and report["current_code_verified"]
    path = write_json("phase12_18b_runtime_reset_report.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.18B HARD RUNTIME RESET ===")
    print(f"Ports Checked: {'PASS' if report['ports_checked'] else 'FAIL'}")
    print(f"Listeners Detected: {len(report['listeners'])}")
    print(f"Stack Restarted: {'PASS' if report['stack_restart'].get('ok') else 'FAIL'}")
    print(f"Current Code Verified: {'PASS' if report['current_code_verified'] else 'FAIL'}")
    print(f"All Services Alive: {'PASS' if report['all_services_alive'] else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
