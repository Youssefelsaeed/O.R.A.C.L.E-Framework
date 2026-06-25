"""Shared helpers for starting and health-checking the ORACLE service stack."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
GUI_DIR = ROOT / "O.R.A.C.L.E_GUi_V1_Figma"
GUI_VALIDATION_DIR = ROOT / "reports" / "final" / "gui_validation"
STACK_LOG_DIR = GUI_VALIDATION_DIR / "logs"

OPTIMIZED_ENV = {
    "PYTHONPATH": str(ROOT),
    "ORACLE_ASYNC_ASSURANCE": "1",
    "GHOSTTUNNEL_FAST_ACK": "1",
    "SERVICE_TIMING_LOG": "0",
    "VITE_ORACLE_API_BASE_URL": "http://127.0.0.1:8000",
}

SERVICE_URLS: Dict[str, str] = {
    "oracle_core": "http://127.0.0.1:8000/docs",
    "qauthcore": "http://127.0.0.1:8001/docs",
    "ethicq": "http://127.0.0.1:8002/docs",
    "chronoledger": "http://127.0.0.1:8003/health",
    "ghosttunnel": "http://127.0.0.1:8004/docs",
}

SERVICE_LABELS: Dict[str, str] = {
    "oracle_core": "Oracle Core",
    "qauthcore": "QAuthCore",
    "ethicq": "EthicQ",
    "chronoledger": "ChronoLedger",
    "ghosttunnel": "GhostTunnel",
}

SERVICES: List[Tuple[str, int, List[str]]] = [
    ("oracle_core", 8000, ["-m", "uvicorn", "oracle_core.main:app", "--host", "127.0.0.1", "--port", "8000"]),
    ("qauthcore", 8001, ["-m", "uvicorn", "qauthcore.main:app", "--host", "127.0.0.1", "--port", "8001"]),
    ("ethicq", 8002, ["-m", "uvicorn", "ethicq.main:app", "--host", "127.0.0.1", "--port", "8002"]),
    ("chronoledger", 8003, ["-m", "uvicorn", "chronoledger.main:app", "--host", "127.0.0.1", "--port", "8003"]),
    ("ghosttunnel", 8004, ["-m", "uvicorn", "ghosttunnel.main:app", "--host", "127.0.0.1", "--port", "8004"]),
]


def merged_env() -> Dict[str, str]:
    return {**dict(os.environ), **OPTIMIZED_ENV}


def kill_port(port: int) -> None:
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, errors="ignore")
        for line in out.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                pid = int(line.split()[-1])
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    except Exception:
        pass


def kill_all_ports() -> None:
    for _name, port, _cmd in SERVICES:
        kill_port(port)
    kill_port(4173)
    time.sleep(1)


def check_health(timeout: float = 3.0) -> Dict[str, bool]:
    result: Dict[str, bool] = {}
    for name, url in SERVICE_URLS.items():
        try:
            r = requests.get(url, timeout=timeout)
            result[name] = r.status_code < 500
        except Exception:
            result[name] = False
    return result


def wait_for_health(max_wait_s: float = 90.0, poll_s: float = 2.0) -> Dict[str, bool]:
    deadline = time.time() + max_wait_s
    status: Dict[str, bool] = {name: False for name in SERVICE_URLS}
    while time.time() < deadline:
        status = check_health()
        if all(status.values()):
            return status
        time.sleep(poll_s)
    return status


def _open_log_pair(name: str) -> Tuple[Any, Any]:
    STACK_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stdout = open(STACK_LOG_DIR / f"{name}.stdout.log", "w", encoding="utf-8", errors="replace")
    stderr = open(STACK_LOG_DIR / f"{name}.stderr.log", "w", encoding="utf-8", errors="replace")
    return stdout, stderr


def start_services() -> List[subprocess.Popen[Any]]:
    env = merged_env()
    procs: List[subprocess.Popen[Any]] = []
    for name, port, cmd in SERVICES:
        stdout, stderr = _open_log_pair(name)
        proc = subprocess.Popen(
            [sys.executable, *cmd],
            cwd=str(ROOT),
            env=env,
            stdout=stdout,
            stderr=stderr,
        )
        setattr(proc, "oracle_service_name", name)
        setattr(proc, "oracle_service_port", port)
        setattr(proc, "oracle_started_at", time.time())
        setattr(proc, "oracle_stdout_log", str(STACK_LOG_DIR / f"{name}.stdout.log"))
        setattr(proc, "oracle_stderr_log", str(STACK_LOG_DIR / f"{name}.stderr.log"))
        procs.append(proc)
    return procs


def start_gui_preview(port: int = 4173) -> Optional[subprocess.Popen[Any]]:
    if not GUI_DIR.exists():
        return None
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    env = merged_env()
    stdout, stderr = _open_log_pair("gui_build")
    subprocess.run([npm, "run", "build"], cwd=str(GUI_DIR), env=env, stdout=stdout, stderr=stderr, check=False)
    stdout, stderr = _open_log_pair("gui")
    proc = subprocess.Popen(
        [npx, "vite", "preview", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(GUI_DIR),
        env=env,
        stdout=stdout,
        stderr=stderr,
    )
    setattr(proc, "oracle_service_name", "gui")
    setattr(proc, "oracle_service_port", port)
    setattr(proc, "oracle_started_at", time.time())
    setattr(proc, "oracle_stdout_log", str(STACK_LOG_DIR / "gui.stdout.log"))
    setattr(proc, "oracle_stderr_log", str(STACK_LOG_DIR / "gui.stderr.log"))
    return proc


def print_service_urls(include_gui: bool = False, gui_port: int = 4173) -> None:
    print("\n=== ORACLE SERVICE URLS ===")
    for name, url in SERVICE_URLS.items():
        print(f"  {SERVICE_LABELS.get(name, name):16} {url.replace('/docs', '').replace('/health', '')}  ({url})")
    print(f"  {'GUI (preview)':16} http://127.0.0.1:{gui_port}")
    if include_gui:
        print(f"\n  Set VITE_ORACLE_API_BASE_URL=http://127.0.0.1:8000 for live dashboard data.")
    print()
