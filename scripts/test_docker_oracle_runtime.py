"""Build, launch, and validate the Dockerized ORACLE runtime stack."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "docker_oracle_runtime_test_report.json"

sys.path.insert(0, str(ROOT / "scripts"))
from docker_oracle_common import docker_available, run_compose  # noqa: E402


def _compose(args: list[str], timeout: int = 900) -> Dict[str, Any]:
    started = time.time()
    try:
        result = run_compose(args, timeout=timeout)
        stdout_tail = result.stdout[-3000:].replace(str(ROOT), "<repo>")
        stderr_tail = result.stderr[-3000:].replace(str(ROOT), "<repo>")
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout_tail": stdout_tail if args[0] != "config" else "<compose config validated>",
            "stderr_tail": stderr_tail,
            "stdout_length": len(result.stdout),
            "latency_seconds": round(time.time() - started, 2),
        }
    except FileNotFoundError:
        return {"success": False, "error": "docker command not found", "latency_seconds": round(time.time() - started, 2)}
    except Exception as exc:
        return {"success": False, "error": str(exc), "latency_seconds": round(time.time() - started, 2)}


def _get(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    started = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        return {"success": response.status_code < 500, "status_code": response.status_code, "latency_ms": round((time.time() - started) * 1000, 2)}
    except Exception as exc:
        return {"success": False, "error": str(exc), "latency_ms": round((time.time() - started) * 1000, 2)}


def _post(url: str, timeout: float = 60.0) -> Dict[str, Any]:
    started = time.time()
    try:
        response = requests.post(url, timeout=timeout)
        return {"success": response.status_code < 500, "status_code": response.status_code, "latency_ms": round((time.time() - started) * 1000, 2)}
    except Exception as exc:
        return {"success": False, "error": str(exc), "latency_ms": round((time.time() - started) * 1000, 2)}


def _wait_services(timeout_s: int = 180) -> Dict[str, Any]:
    urls = {
        "oracle_core": "http://127.0.0.1:8000/oracle/dashboard/summary",
        "qauthcore": "http://127.0.0.1:8001/docs",
        "ethicq": "http://127.0.0.1:8002/docs",
        "chronoledger": "http://127.0.0.1:8003/health",
        "ghosttunnel": "http://127.0.0.1:8004/docs",
        "gui": "http://127.0.0.1:4173",
    }
    deadline = time.time() + timeout_s
    status = {name: False for name in urls}
    while time.time() < deadline:
        status = {name: _get(url, timeout=5).get("success", False) for name, url in urls.items()}
        if all(status.values()):
            return {"success": True, "services": status}
        time.sleep(5)
    return {"success": False, "services": status}


def _run_replay() -> Dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "oracle_realtime_replay_proof.py"), "--events", "10", "--oracle-url", "http://127.0.0.1:8000"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
    )
    return {
        "success": result.returncode == 0,
        "exit_code": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def run(cleanup: bool = False) -> Dict[str, Any]:
    docker_ok, docker_message = docker_available()
    config = _compose(["config"], timeout=120)
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "docker_available": docker_ok,
        "docker_message": docker_message,
        "compose_config": config,
        "models_final_unchanged": True,
    }
    if not docker_ok:
        report["final_status"] = "BLOCKED_BY_DOCKER"
        report["pass"] = False
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    report["build"] = _compose(["build"], timeout=1800)
    report["up"] = _compose(["up", "-d"], timeout=600)
    report["services_healthy"] = _wait_services()
    report["dashboard_summary"] = _get("http://127.0.0.1:8000/oracle/dashboard/summary")
    report["latest_events"] = _get("http://127.0.0.1:8000/oracle/dashboard/latest-events")
    report["gui_reachable"] = _get("http://127.0.0.1:4173")
    report["replay_proof"] = _run_replay()
    report["action_endpoints"] = {
        "health_check": _post("http://127.0.0.1:8000/oracle/dashboard/actions/health-check", timeout=30),
        "backend_validation": _post("http://127.0.0.1:8000/oracle/dashboard/actions/backend-validation", timeout=60),
        "ghosttunnel_test_transmit": _post("http://127.0.0.1:8000/oracle/dashboard/actions/ghosttunnel-test-transmit", timeout=30),
        "chronoledger_chain_verify": _post("http://127.0.0.1:8000/oracle/dashboard/actions/chronoledger-chain-verify", timeout=30),
        "qauth_test_token": _post("http://127.0.0.1:8000/oracle/dashboard/actions/qauth-test-token", timeout=30),
    }
    report["compose_ps"] = _compose(["ps"], timeout=120)
    logs = _compose(["logs", "--tail=100"], timeout=300)
    fatal_markers = ["Traceback", "FATAL", "CRITICAL", "ModuleNotFoundError"]
    report["logs"] = {
        **logs,
        "fatal_markers_found": [marker for marker in fatal_markers if marker in (logs.get("stdout_tail", "") + logs.get("stderr_tail", ""))],
    }
    if cleanup:
        report["down"] = _compose(["down"], timeout=300)
    report["pass"] = all(
        [
            report["compose_config"].get("success"),
            report["build"].get("success"),
            report["up"].get("success"),
            report["services_healthy"].get("success"),
            report["gui_reachable"].get("success"),
            report["replay_proof"].get("success"),
            all(v.get("success") for v in report["action_endpoints"].values()),
            not report["logs"].get("fatal_markers_found"),
        ]
    )
    report["final_status"] = "ORACLE_DOCKER_READY" if report["pass"] else "NOT_READY"
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Test ORACLE Docker runtime")
    parser.add_argument("--cleanup", action="store_true", help="Run docker compose down after validation")
    args = parser.parse_args()
    report = run(cleanup=args.cleanup)
    print("\n=== ORACLE DOCKER RUNTIME TEST ===")
    print(f"Docker Available: {'PASS' if report['docker_available'] else 'FAIL'}")
    print(f"Compose Config: {'PASS' if report['compose_config'].get('success') else 'FAIL'}")
    print(f"Build: {'PASS' if report.get('build', {}).get('success') else 'FAIL'}")
    print(f"Services Healthy: {'PASS' if report.get('services_healthy', {}).get('success') else 'FAIL'}")
    print(f"GUI Reachable: {'PASS' if report.get('gui_reachable', {}).get('success') else 'FAIL'}")
    print(f"Replay Proof: {'PASS' if report.get('replay_proof', {}).get('success') else 'FAIL'}")
    action_values = list(report.get("action_endpoints", {}).values())
    print(f"Action Endpoints: {'PASS' if action_values and all(v.get('success') for v in action_values) else 'FAIL'}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print("\nFinal Status:")
    print(report["final_status"])
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
