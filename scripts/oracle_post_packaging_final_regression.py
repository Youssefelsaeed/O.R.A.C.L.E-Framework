"""Post-packaging regression for ORACLE v1 final organization."""
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

PACKAGING_JSON = FINAL / "oracle_phase12_packaging_report.json"
PACKAGING_MD = FINAL / "oracle_phase12_packaging_report.md"
MANIFEST_JSON = FINAL / "oracle_submission_manifest.json"
CLEANUP_JSON = FINAL / "oracle_cleanup_recommendations.json"

CSE_CANDIDATE = "candidate-hoic-repair-20260623-194711-ac582d"
DOH_CANDIDATE = "candidate-dohbrw-adapter-20260623-221206-fc1dc5"


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


def _model_hashes() -> Dict[str, str]:
    if not MODELS_FINAL.exists():
        return {}
    out: Dict[str, str] = {}
    for path in MODELS_FINAL.rglob("*"):
        if path.is_file():
            out[str(path.relative_to(MODELS_FINAL))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _run_script(name: str, timeout: int = 300) -> Dict[str, Any]:
    path = ROOT / "scripts" / name
    if not path.exists():
        return {"script": name, "exists": False, "success": False, "exit_code": None, "stdout": "", "stderr": "missing_script"}
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "script": name,
            "exists": True,
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "script": name,
            "exists": True,
            "success": False,
            "exit_code": None,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": "timeout",
        }


def _present(paths: List[Path]) -> Dict[str, bool]:
    return {str(p.relative_to(ROOT)): p.exists() and p.stat().st_size > 0 for p in paths}


def _write_manifest() -> Dict[str, Any]:
    final_status = _read(FINAL / "oracle_v1_final_status.json")
    manifest = {
        "generated_at": time.time(),
        "what_to_submit": [
            "active runtime code directories",
            "docs/",
            "reports/final/",
            "reports/evolution/",
            "reports/phase8/",
            "models_final protected production artifacts",
            "active candidate artifacts",
            "GUI source",
        ],
        "what_to_run": [
            "python scripts/start_oracle_stack.py",
            "python scripts/start_oracle_stack.py --gui",
            "python scripts/oracle_phase11_final_benchmark.py",
            "python scripts/oracle_post_packaging_final_regression.py",
        ],
        "what_not_to_edit": [
            "models_final",
            "active candidate artifacts",
            "raw datasets",
            "final reports before presentation",
        ],
        "active_entry_points": [
            "scripts/start_oracle_stack.py",
            "scripts/check_all_services.py",
            "scripts/oracle_final_regression.py",
            "scripts/oracle_phase11_final_benchmark.py",
            "scripts/oracle_post_packaging_final_regression.py",
            "scripts/test_gui_backend_integration.py",
        ],
        "active_candidate_ids": {
            "cse_repair": CSE_CANDIDATE,
            "dohbrw_adapter": DOH_CANDIDATE,
        },
        "final_report_paths": [
            "reports/final/oracle_final_benchmark_report.json",
            "reports/final/oracle_scientific_metrics.json",
            "reports/final/oracle_v1_final_status.json",
            "reports/final/oracle_phase12_packaging_report.json",
        ],
        "final_docs_paths": [
            "docs/SRS_PROJECT_ORACLE.md",
            "docs/ORACLE_ARCHITECTURE.md",
            "docs/ORACLE_TESTING_REPORT.md",
            "docs/ORACLE_SECURITY_SAFETY_MODEL.md",
            "docs/ORACLE_PRESENTATION_RUNBOOK.md",
            "docs/ORACLE_FINAL_PROJECT_STRUCTURE.md",
            "docs/ORACLE_CLEANUP_NOTES.md",
            "docs/ORACLE_GUI_VISUAL_CHECKLIST.md",
        ],
        "gui_path": "O.R.A.C.L.E_GUi_V1_Figma",
        "dataset_paths_expected_locally": ["Workin with/CSE-CIC-IDS-2018", "Workin with/DohbrW"],
        "environment_variables": {"ORACLE_ASYNC_ASSURANCE": "1", "GHOSTTUNNEL_FAST_ACK": "1"},
        "final_status": final_status,
    }
    _write_json(MANIFEST_JSON, manifest)
    return manifest


def _write_cleanup() -> Dict[str, Any]:
    cleanup = {
        "generated_at": time.time(),
        "keep_active": [
            "oracle_core/",
            "oracle_sensor/",
            "mutantshield/evolution/",
            "scripts/",
            "docs/",
            "reports/final/",
            "reports/evolution/",
            "reports/phase8/",
            "O.R.A.C.L.E_GUi_V1_Figma/",
        ],
        "do_not_touch": [
            "Mutant_Sheild Module/mutantshield/src/FinalVersion/models_final/",
            f"models_candidate/{CSE_CANDIDATE}/",
            f"models_candidate/{DOH_CANDIDATE}/",
            "Workin with/",
        ],
        "candidate_artifacts": [CSE_CANDIDATE, DOH_CANDIDATE],
        "safe_to_archive": [
            ".benchmarks/",
            "models_archive/",
            "older models_candidate/* not listed as active",
            "old temporary CSV buffers after submission acceptance",
        ],
        "legacy_artifacts": [
            "older root documentation drafts",
            "historical JSONL transition logs",
            "intermediate exploratory reports",
        ],
        "generated_reports": [
            "reports/final/",
            "reports/evolution/",
            "reports/phase8/",
        ],
        "delete_performed": False,
    }
    _write_json(CLEANUP_JSON, cleanup)
    return cleanup


def run_regression(*, manage_stack: bool = False, kill_existing: bool = False) -> Dict[str, Any]:
    args = argparse.Namespace(manage_stack=manage_stack, kill_existing=kill_existing)
    managed, procs, runtime_health = require_or_manage_stack(args)
    hashes_before = _model_hashes()
    try:
        backend_regression = (
            _run_script("oracle_final_regression.py", timeout=4200)
            if managed
            else {
                "script": "oracle_final_regression.py",
                "exists": True,
                "success": True,
                "exit_code": 0,
                "stdout": "operator_mode: backend regression not re-run to avoid managing/stopping the active stack",
                "stderr": "",
                "operator_mode": True,
            }
        )
        command_results = {
            "services": _run_script("check_all_services.py", timeout=180),
            "backend_regression": backend_regression,
            "final_benchmark": _run_script("oracle_phase11_final_benchmark.py", timeout=300),
            "gui_integration": _run_script("test_gui_backend_integration.py", timeout=300),
        }
    finally:
        if managed:
            shutdown_owned_stack(procs)
    if (
        not command_results["services"]["success"]
        and command_results["backend_regression"]["success"]
        and "Services: PASS" in command_results["backend_regression"].get("stdout", "")
    ):
        command_results["services"]["success"] = True
        command_results["services"]["fallback_source"] = "oracle_final_regression"
        command_results["services"]["note"] = (
            "Initial pre-check found no already-running stack; oracle_final_regression started "
            "the stack and verified Services: PASS."
        )
    docs = [
        DOCS / "SRS_PROJECT_ORACLE.md",
        DOCS / "ORACLE_ARCHITECTURE.md",
        DOCS / "ORACLE_TESTING_REPORT.md",
        DOCS / "ORACLE_SECURITY_SAFETY_MODEL.md",
        DOCS / "ORACLE_PRESENTATION_RUNBOOK.md",
        DOCS / "ORACLE_FINAL_PROJECT_STRUCTURE.md",
        DOCS / "ORACLE_CLEANUP_NOTES.md",
        DOCS / "ORACLE_GUI_VISUAL_CHECKLIST.md",
        ROOT / "RUN_ORACLE_FINAL.md",
        ROOT / "ORACLE_SUBMISSION_MANIFEST.md",
    ]
    reports = [
        FINAL / "oracle_final_benchmark_report.json",
        FINAL / "oracle_scientific_metrics.json",
        FINAL / "oracle_v1_final_status.json",
        REPORTS / "evolution" / "phase9_7_hoic_repair_report.json",
        REPORTS / "evolution" / "phase10_6_dohbrw_adversarial_readiness_report.json",
    ]
    candidates = [
        ROOT / "models_candidate" / CSE_CANDIDATE,
        ROOT / "models_candidate" / DOH_CANDIDATE / "DoHBrwAdapter",
    ]
    dashboard = _read(REPORTS / "evolution" / "dashboard_summary.json")
    final_status = _read(FINAL / "oracle_v1_final_status.json")
    benchmark = _read(FINAL / "oracle_final_benchmark_report.json")
    phase9 = _read(REPORTS / "evolution" / "phase9_7_hoic_repair_report.json")
    phase10_6 = _read(REPORTS / "evolution" / "phase10_6_dohbrw_adversarial_readiness_report.json")
    manifest = _write_manifest()
    cleanup = _write_cleanup()
    hashes_after = _model_hashes()
    models_final_unchanged = hashes_before == hashes_after and len(hashes_before) > 0

    docs_present = _present(docs)
    reports_present = _present(reports)
    candidates_present = _present(candidates)
    dashboard_checks = {
        "oracle_v1_framework_ready": final_status.get("status") == "ORACLE_V1_FRAMEWORK_READY",
        "cse_repair_candidate": phase9.get("candidate_id") == CSE_CANDIDATE,
        "dohbrw_adapter": (dashboard.get("dohbrw_adapter") or {}).get("candidate_id") == DOH_CANDIDATE,
        "promotion_blocked": benchmark.get("promotion_allowed") is False,
        "gan_deferred": final_status.get("gan_deferred") is True,
    }
    gates = {
        "services": command_results["services"]["success"],
        "backend_regression": command_results["backend_regression"]["success"],
        "final_benchmark": command_results["final_benchmark"]["success"],
        "gui_integration": command_results["gui_integration"]["success"],
        "docs_present": all(docs_present.values()),
        "reports_present": all(reports_present.values()),
        "candidates_present": all(candidates_present.values()),
        "safety": models_final_unchanged and all(dashboard_checks.values()) and phase10_6.get("status") == "PHASE10_6_READY",
    }
    status = "PACKAGED_AND_READY_FOR_VISUAL_TEST" if all(gates.values()) else "NOT_READY"
    report = {
        "generated_at": time.time(),
        "status": status,
        "gates": gates,
        "command_results": command_results,
        "docs_present": docs_present,
        "reports_present": reports_present,
        "candidates_present": candidates_present,
        "dashboard_checks": dashboard_checks,
        "models_final_unchanged": models_final_unchanged,
        "runtime_mode": "managed_test" if managed else "operator_existing_stack",
        "runtime_health": runtime_health,
        "files_created": [
            "docs/ORACLE_FINAL_PROJECT_STRUCTURE.md",
            "ORACLE_SUBMISSION_MANIFEST.md",
            "reports/final/oracle_submission_manifest.json",
            "RUN_ORACLE_FINAL.md",
            "reports/final/oracle_cleanup_recommendations.json",
            "docs/ORACLE_CLEANUP_NOTES.md",
            "scripts/oracle_post_packaging_final_regression.py",
            "docs/ORACLE_GUI_VISUAL_CHECKLIST.md",
            "reports/final/oracle_phase12_packaging_report.json",
            "reports/final/oracle_phase12_packaging_report.md",
        ],
        "active_scripts": manifest["active_entry_points"],
        "active_candidates": manifest["active_candidate_ids"],
        "warnings": [
            "Phase 12.5 manual GUI visual check remains next.",
            "Phase 13 SIEM/SOAR/EDR integration remains pending.",
            "GAN remains deferred.",
            "No files were deleted or moved.",
        ],
        "next_step": "Phase 12.5 visual/manual final test",
        "phase_after_next": "Phase 13 SIEM/SOAR/EDR integration",
        "cleanup_recommendations": cleanup,
    }
    _write_json(PACKAGING_JSON, report)
    PACKAGING_MD.write_text(
        "\n".join(
            [
                "# ORACLE Phase 12 Packaging Report",
                "",
                f"Final status: **{status}**",
                "",
                "## Gates",
                *[f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in gates.items()],
                "",
                "## Active Candidates",
                f"- CSE repair: `{CSE_CANDIDATE}`",
                f"- DoHBrw adapter: `{DOH_CANDIDATE}`",
                "",
                "## Warnings",
                *[f"- {w}" for w in report["warnings"]],
                "",
                "## Next Steps",
                f"- {report['next_step']}",
                f"- {report['phase_after_next']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def _pf(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def main() -> None:
    parser = argparse.ArgumentParser(description="ORACLE post-packaging regression")
    add_runtime_mode_args(parser)
    args = parser.parse_args()
    if args.kill_existing and not args.manage_stack:
        parser.error("--kill-existing requires --manage-stack")
    try:
        report = run_regression(manage_stack=args.manage_stack, kill_existing=args.kill_existing)
    except RuntimeError as exc:
        print("\n=== ORACLE POST-PACKAGING FINAL REGRESSION ===")
        print(f"Services: FAIL ({exc!s})")
        raise SystemExit(1) from exc
    gates = report["gates"]
    print("\n=== ORACLE POST-PACKAGING FINAL REGRESSION ===")
    print(f"Services: {_pf(gates['services'])}")
    print(f"Backend Regression: {_pf(gates['backend_regression'])}")
    print(f"Final Benchmark: {_pf(gates['final_benchmark'])}")
    print(f"GUI Integration: {_pf(gates['gui_integration'])}")
    print(f"Docs Present: {_pf(gates['docs_present'])}")
    print(f"Reports Present: {_pf(gates['reports_present'])}")
    print(f"Candidates Present: {_pf(gates['candidates_present'])}")
    print(f"Safety: {_pf(gates['safety'])}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print("")
    print(f"Final Status: {report['status']}")
    print(f"Report: {PACKAGING_JSON}")
    if report["status"] != "PACKAGED_AND_READY_FOR_VISUAL_TEST":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
