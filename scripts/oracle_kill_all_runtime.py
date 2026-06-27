"""Stop ORACLE-owned local runtime processes without deleting local files."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
PORTS = [8000, 8001, 8002, 8003, 8004, 4173]
ORACLE_MARKERS = [
    str(ROOT).lower(),
    "oracle_core",
    "qauthcore",
    "ethicq",
    "chronoledger",
    "ghosttunnel",
    "oracle_sensor",
    "start_oracle_stack",
    "uvicorn",
    "vite",
    "node.exe",
]


def run_cmd(args: List[str], timeout: int = 30) -> Dict[str, Any]:
    try:
        proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        return {
            "cmd": args,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-8000:],
            "stderr": proc.stderr[-4000:],
        }
    except Exception as exc:
        return {"cmd": args, "exit_code": None, "error": f"{type(exc).__name__}:{exc}"}


def netstat_listeners() -> Dict[str, Any]:
    result = run_cmd(["netstat", "-ano", "-p", "tcp"])
    listeners: List[Dict[str, Any]] = []
    for line in str(result.get("stdout", "")).splitlines():
        if "LISTENING" not in line.upper():
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        local = parts[1]
        for port in PORTS:
            if local.endswith(f":{port}"):
                listeners.append({"method": "netstat", "port": port, "pid": int(parts[-1]), "line": line})
    result["listeners"] = listeners
    return result


def tcp_connection_listeners() -> Dict[str, Any]:
    ps = (
        "Get-NetTCPConnection -State Listen -LocalPort "
        + ",".join(str(p) for p in PORTS)
        + " -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess | ConvertTo-Json"
    )
    result = run_cmd(["powershell", "-NoProfile", "-Command", ps])
    listeners: List[Dict[str, Any]] = []
    try:
        parsed = json.loads(str(result.get("stdout") or "[]"))
        if isinstance(parsed, dict):
            parsed = [parsed]
        for item in parsed or []:
            listeners.append(
                {
                    "method": "Get-NetTCPConnection",
                    "port": int(item.get("LocalPort")),
                    "pid": int(item.get("OwningProcess")),
                }
            )
    except Exception as exc:
        result["parse_error"] = str(exc)
    result["listeners"] = listeners
    return result


def listeners() -> List[Dict[str, Any]]:
    seen: Dict[tuple[int, int], Dict[str, Any]] = {}
    for source in (netstat_listeners(), tcp_connection_listeners()):
        for item in source.get("listeners", []):
            seen[(item["port"], item["pid"])] = item
    return list(seen.values())


def pid_details(pid: int) -> Dict[str, Any]:
    details: Dict[str, Any] = {"pid": pid}
    details["tasklist"] = run_cmd(["tasklist", "/FI", f"PID eq {pid}", "/V"])
    details["wmic"] = run_cmd(["wmic", "process", "where", f"processid={pid}", "get", "ProcessId,Name,CommandLine", "/FORMAT:LIST"])
    ps = f"Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\" | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json"
    details["powershell_process"] = run_cmd(["powershell", "-NoProfile", "-Command", ps])
    text = " ".join(str(details[k].get("stdout", "")) for k in ("tasklist", "wmic", "powershell_process")).lower()
    details["process_name"] = _first_process_name(text)
    details["oracle_related"] = any(marker in text for marker in ORACLE_MARKERS)
    details["resolved"] = any(str(pid) in str(details[k].get("stdout", "")) for k in ("tasklist", "wmic", "powershell_process"))
    return details


def _first_process_name(text: str) -> str | None:
    for token in ("python.exe", "python", "node.exe", "node", "uvicorn.exe", "powershell.exe"):
        if token in text:
            return token
    return None


def stop_pid(pid: int, oracle_related: bool) -> Dict[str, Any]:
    if not oracle_related:
        return {"pid": pid, "skipped": True, "reason": "not_oracle_related"}
    return {
        "pid": pid,
        "skipped": False,
        "taskkill": run_cmd(["taskkill", "/PID", str(pid), "/T", "/F"]),
        "stop_process": run_cmd(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction Continue"]),
    }


def kill_oracle_runtime() -> Dict[str, Any]:
    initial_sources = {"netstat": netstat_listeners(), "get_net_tcp": tcp_connection_listeners()}
    found = listeners()
    details = [pid_details(item["pid"]) for item in found]
    detail_by_pid = {item["pid"]: item for item in details}
    kills = [stop_pid(item["pid"], bool(detail_by_pid.get(item["pid"], {}).get("oracle_related"))) for item in found]
    time.sleep(2)
    remaining = listeners()
    return {
        "generated_at": time.time(),
        "ports": PORTS,
        "initial_sources": initial_sources,
        "listeners": found,
        "pid_details": details,
        "kill_attempts": kills,
        "remaining_listeners": remaining,
        "all_oracle_listeners_stopped": not any(detail_by_pid.get(item["pid"], {}).get("oracle_related") for item in remaining),
    }


def main() -> None:
    report = kill_oracle_runtime()
    print("=== ORACLE RUNTIME KILL ===")
    for item in report["listeners"]:
        details = next((d for d in report["pid_details"] if d["pid"] == item["pid"]), {})
        print(
            f"port={item['port']} pid={item['pid']} "
            f"oracle_related={details.get('oracle_related')} resolved={details.get('resolved')}"
        )
    print(f"Remaining listeners: {len(report['remaining_listeners'])}")
    print(f"All ORACLE listeners stopped: {report['all_oracle_listeners_stopped']}")
    if not report["all_oracle_listeners_stopped"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
