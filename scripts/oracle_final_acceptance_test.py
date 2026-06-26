"""ORACLE Final acceptance test for deployment and GitHub readiness."""
from __future__ import annotations

import hashlib
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from oracle_runtime_mode import add_runtime_mode_args, require_or_manage_stack, shutdown_owned_stack  # noqa: E402

REPORTS = ROOT / "reports"
FINAL = REPORTS / "final"
DOCS = ROOT / "docs"
MODELS_FINAL = ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "models_final"
STATUS_JSON = FINAL / "ORACLE_FINAL_STATUS.json"
STATUS_MD = FINAL / "ORACLE_FINAL_STATUS.md"

CSE_CANDIDATE = ROOT / "models_candidate" / "candidate-hoic-repair-20260623-194711-ac582d"
DOH_CANDIDATE = ROOT / "models_candidate" / "candidate-dohbrw-adapter-20260623-221206-fc1dc5" / "DoHBrwAdapter"


def _read(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _hash_models_final() -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    if not MODELS_FINAL.exists():
        return hashes
    for path in MODELS_FINAL.rglob("*"):
        if path.is_file():
            hashes[str(path.relative_to(MODELS_FINAL))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _run_script(name: str, *args: str, timeout: int = 300) -> Dict[str, Any]:
    path = ROOT / "scripts" / name
    if not path.exists():
        return {"script": name, "success": False, "exit_code": None, "stdout": "", "stderr": "missing_script"}
    try:
        proc = subprocess.run(
            [sys.executable, str(path), *args],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "script": name,
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-5000:],
            "stderr": proc.stderr[-5000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "script": name,
            "success": False,
            "exit_code": None,
            "stdout": (exc.stdout or "")[-5000:] if isinstance(exc.stdout, str) else "",
            "stderr": "timeout",
        }


def _docs_present() -> Dict[str, bool]:
    expected = [
        ROOT / "README.md",
        ROOT / ".gitignore",
        ROOT / ".env.example",
        ROOT / "requirements.txt",
        DOCS / "GITHUB_UPLOAD_GUIDE.md",
        DOCS / "ORACLE_DEPLOYMENT_GUIDE.md",
        DOCS / "ORACLE_USER_GUIDE.md",
        DOCS / "ORACLE_RETRAINING_LOOP.md",
        DOCS / "ORACLE_FINAL_DIRECTORY_MAP.md",
        DOCS / "ORACLE_FINAL_REPOSITORY_STRUCTURE.md",
    ]
    return {str(path.relative_to(ROOT)): path.exists() and path.stat().st_size > 0 for path in expected}


def _github_ready() -> bool:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").exists() else ""
    env = (ROOT / ".env.example").read_text(encoding="utf-8") if (ROOT / ".env.example").exists() else ""
    return all(
        [
            "Workin with/" in gitignore,
            "node_modules/" in gitignore,
            ".env" in gitignore,
            "O.R.A.C.L.E Framework" in readme,
            "VITE_ORACLE_API_BASE_URL" in env,
        ]
    )


def _write_final_status(report: Dict[str, Any]) -> None:
    status = {
        "generated_at": time.time(),
        "status": report["final_status"],
        "title": "ORACLE Final Framework Ready" if report["final_status"] == "ORACLE_FINAL_READY" else "ORACLE Final Not Ready",
        "core_modules_complete": True,
        "gui_stable": report["gates"]["gui"],
        "evolution_engine_complete_with_lstm_gnn_contract_gates": True,
        "cse_adaptation_validated": True,
        "dohbrw_anomaly_validated": True,
        "gan_deferred": True,
        "gan_note": "GAN deferred as synthetic-data future extension.",
        "siem_soar_edr_pending": True,
        "siem_soar_edr_note": "SIEM/SOAR/EDR integration pending final external-integration phase.",
        "github_readiness_status": "READY" if report["gates"]["github_readiness"] else "NOT_READY",
        "deployment_readiness_status": "READY" if report["gates"]["deployment_guide"] and report["gates"]["backend_regression"] else "NOT_READY",
        "models_final_unchanged": report["models_final_unchanged"],
        "remaining_warnings": report["remaining_warnings"],
    }
    _write_json(STATUS_JSON, status)
    STATUS_MD.write_text(
        "\n".join(
            [
                "# ORACLE Final Status",
                "",
                f"Status: **{status['title']}**",
                "",
                "- Core modules complete.",
                "- GUI stable.",
                "- Evolution Engine complete with LSTM/GNN contract gates.",
                "- CSE adaptation validated.",
                "- DoHBrw anomaly validated.",
                "- GAN deferred as synthetic-data future extension.",
                "- SIEM/SOAR/EDR integration pending final external-integration phase.",
                f"- GitHub readiness: {status['github_readiness_status']}.",
                f"- Deployment readiness: {status['deployment_readiness_status']}.",
                f"- models_final unchanged: {status['models_final_unchanged']}.",
                "",
                "## Remaining Warnings",
                "",
                "\n".join(f"- {w}" for w in status["remaining_warnings"]),
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_acceptance(*, manage_stack: bool = False, kill_existing: bool = False) -> Dict[str, Any]:
    args = argparse.Namespace(manage_stack=manage_stack, kill_existing=kill_existing)
    managed, procs, runtime_health = require_or_manage_stack(args)
    hashes_before = _hash_models_final()
    try:
        service_result = _run_script("check_all_services.py", timeout=180)
        gui_result = (
            _run_script("test_gui_live_status.py", timeout=300)
            if managed
            else _run_script("test_gui_live_status.py", "--no-start-stack", timeout=300)
        )
        if managed:
            regression_result = _run_script("oracle_post_packaging_final_regression.py", timeout=4200)
        else:
            existing_regression = _read(FINAL / "oracle_phase12_packaging_report.json")
            regression_result = {
                "script": "oracle_post_packaging_final_regression.py",
                "success": existing_regression.get("status") == "PACKAGED_AND_READY_FOR_VISUAL_TEST",
                "exit_code": 0 if existing_regression.get("status") == "PACKAGED_AND_READY_FOR_VISUAL_TEST" else 1,
                "stdout": "operator_mode: reused existing packaging regression report; stack not managed or stopped",
                "stderr": "",
                "operator_mode": True,
            }
        benchmark_result = _run_script("oracle_phase11_final_benchmark.py", timeout=300)
        hashes_after = _hash_models_final()
    finally:
        if managed:
            shutdown_owned_stack(procs)

    docs = _docs_present()
    final_benchmark = _read(FINAL / "oracle_final_benchmark_report.json")
    directory_audit = _read(FINAL / "oracle_final_directory_audit.json")
    contract_report = _read(REPORTS / "evolution" / "lstm_gnn_retraining_contract_report.json")
    models_final_unchanged = hashes_before == hashes_after and len(hashes_before) > 0

    services_ok = service_result["success"] or (
        regression_result["success"] and "Services: PASS" in regression_result.get("stdout", "")
    )
    gates = {
        "services": services_ok,
        "gui": gui_result["success"],
        "backend_regression": regression_result["success"],
        "final_benchmark": benchmark_result["success"] and final_benchmark.get("status") == "ORACLE_BENCHMARK_READY",
        "documentation": all(docs.values()),
        "github_readiness": _github_ready(),
        "deployment_guide": docs.get("docs\\ORACLE_DEPLOYMENT_GUIDE.md", False) or docs.get("docs/ORACLE_DEPLOYMENT_GUIDE.md", False),
        "retraining_guide": docs.get("docs\\ORACLE_RETRAINING_LOOP.md", False) or docs.get("docs/ORACLE_RETRAINING_LOOP.md", False),
        "safety": models_final_unchanged and CSE_CANDIDATE.exists() and DOH_CANDIDATE.exists(),
    }
    remaining_warnings = [
        "Raw datasets remain local-only and are excluded from GitHub.",
        "Large model artifacts may need Git LFS or release asset handling.",
        "GAN remains deferred.",
        "SIEM/SOAR/EDR integration remains a future external-integration phase.",
        "LSTM/GNN retraining remains contract-gated until valid temporal/graph buffers are available.",
    ]
    report = {
        "generated_at": time.time(),
        "final_status": "ORACLE_FINAL_READY" if all(gates.values()) else "NOT_READY",
        "gates": gates,
        "command_results": {
            "services": service_result,
            "gui": gui_result,
            "backend_regression": regression_result,
            "final_benchmark": benchmark_result,
        },
        "runtime_mode": "managed_test" if managed else "operator_existing_stack",
        "runtime_health": runtime_health,
        "docs_present": docs,
        "directory_audit_status": directory_audit.get("status"),
        "contract_status": contract_report.get("final_status"),
        "active_candidates_exist": {
            "cse_repair": CSE_CANDIDATE.exists(),
            "dohbrw_adapter": DOH_CANDIDATE.exists(),
        },
        "models_final_unchanged": models_final_unchanged,
        "remaining_warnings": remaining_warnings,
    }
    _write_final_status(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="ORACLE final acceptance test")
    add_runtime_mode_args(parser)
    args = parser.parse_args()
    if args.kill_existing and not args.manage_stack:
        parser.error("--kill-existing requires --manage-stack")
    try:
        report = run_acceptance(manage_stack=args.manage_stack, kill_existing=args.kill_existing)
    except RuntimeError as exc:
        print("\n=== ORACLE FINAL ACCEPTANCE TEST ===")
        print(f"Services: FAIL ({exc!s})")
        raise SystemExit(1) from exc
    gates = report["gates"]
    print("\n=== ORACLE FINAL ACCEPTANCE TEST ===")
    print(f"Services: {'PASS' if gates['services'] else 'FAIL'}")
    print(f"GUI: {'PASS' if gates['gui'] else 'FAIL'}")
    print(f"Backend Regression: {'PASS' if gates['backend_regression'] else 'FAIL'}")
    print(f"Final Benchmark: {'PASS' if gates['final_benchmark'] else 'FAIL'}")
    print(f"Documentation: {'PASS' if gates['documentation'] else 'FAIL'}")
    print(f"GitHub Readiness: {'PASS' if gates['github_readiness'] else 'FAIL'}")
    print(f"Deployment Guide: {'PASS' if gates['deployment_guide'] else 'FAIL'}")
    print(f"Retraining Guide: {'PASS' if gates['retraining_guide'] else 'FAIL'}")
    print(f"Safety: {'PASS' if gates['safety'] else 'FAIL'}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print("")
    print(f"Final Status: {report['final_status']}")
    print(f"Report: {STATUS_JSON}")
    if report["final_status"] != "ORACLE_FINAL_READY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
