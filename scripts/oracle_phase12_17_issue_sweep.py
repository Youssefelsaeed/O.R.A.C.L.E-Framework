"""Phase 12.17 final issue and safety sweep."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import time
from typing import Any, Dict, List

from oracle_phase12_17_common import ROOT, model_hashes, write_report

FORBIDDEN_STAGE_RE = re.compile(
    r"(^|/)(Workin with|node_modules|\.venv|venv|__pycache__|Diagrams)(/|$)|"
    r"(^|/)\.env$|"
    r"\.(pkl|joblib|pth|pt|onnx|keras|h5|pcap|pcapng|parquet|feather|arff|zip|7z|tar|gz)$",
    re.IGNORECASE,
)


def _git(args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, timeout=60)


def run() -> Dict[str, Any]:
    status = _git(["status", "--short"]).stdout.splitlines()
    staged = _git(["diff", "--cached", "--name-only"]).stdout.splitlines()
    docker_info = subprocess.run(["docker", "info"], cwd=ROOT, text=True, capture_output=True, timeout=20)
    scapy_installed = importlib.util.find_spec("scapy") is not None
    model_hash_count = len(model_hashes())
    forbidden_staged = [path for path in staged if FORBIDDEN_STAGE_RE.search(path.replace("\\", "/"))]
    model_staged = [path for path in staged if "models_final" in path.replace("\\", "/")]
    warnings = {
        "docker_runtime": "blocked_if_docker_engine_unavailable" if docker_info.returncode != 0 else "available",
        "live_packet_capture": "blocked_if_scapy_npcap_admin_unavailable" if not scapy_installed else "dependencies_present",
        "gan": "deferred",
        "lstm_gnn": "contract_gated",
        "siem_soar_edr": "documented_future_integration",
    }
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "models_final_hash_count": model_hash_count,
        "models_final_unchanged": model_hash_count > 0 and not model_staged,
        "git_status_summary": status[:200],
        "staged_files": staged,
        "forbidden_staged_files": forbidden_staged,
        "raw_datasets_staged": [path for path in staged if "Workin with" in path or path.lower().endswith((".pcap", ".pcapng", ".parquet"))],
        "env_staged": [path for path in staged if path.endswith(".env") or path == ".env"],
        "known_warnings": warnings,
    }
    report["pass"] = bool(report["models_final_unchanged"]) and not forbidden_staged and not report["raw_datasets_staged"] and not report["env_staged"]
    path = write_report("phase12_17_issue_sweep.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.17 ISSUE SWEEP ===")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print(f"Forbidden staged files: {len(report['forbidden_staged_files'])}")
    print(f"Raw datasets staged: {len(report['raw_datasets_staged'])}")
    print(f".env staged: {len(report['env_staged'])}")
    for name, value in report["known_warnings"].items():
        print(f"{name}: {value}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
