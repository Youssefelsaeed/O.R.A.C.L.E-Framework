"""Audit and optionally clean the public GitHub repository scope."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "final"
POLICY_PATH = ROOT / "docs" / "GITHUB_REPO_SCOPE_POLICY.md"

ESSENTIAL_SCRIPT_ALLOWLIST = {
    "scripts/start_oracle_stack.py",
    "scripts/oracle_stack_common.py",
    "scripts/oracle_runtime_mode.py",
    "scripts/oracle_kill_all_runtime.py",
    "scripts/oracle_runtime_current_code_check.py",
    "scripts/oracle_github_repo_scope_audit.py",
    "scripts/oracle_realtime_replay_proof.py",
    "scripts/oracle_live_sensor_smoke_test.py",
    "scripts/oracle_final_acceptance_test.py",
    "scripts/docker_oracle_common.py",
    "scripts/docker_oracle_up.py",
    "scripts/docker_oracle_down.py",
    "scripts/docker_oracle_status.py",
    "scripts/docker_oracle_logs.py",
}

ESSENTIAL_DOCS = {
    "docs/ARCHITECTURE.md",
    "docs/DEPLOYMENT.md",
    "docs/USER_GUIDE.md",
    "docs/SECURITY_MODEL.md",
    "docs/TESTING_AND_VALIDATION.md",
    "docs/MODULE_CAPABILITIES.md",
    "docs/RETRAINING_AND_EVOLUTION.md",
    "docs/SIEM_SOAR_EDR_INTEGRATION.md",
    "docs/ROADMAP.md",
    "docs/ORACLE_GUI_LIVE_DEMO_SCRIPT.md",
    "docs/FINAL_DETECTION_RESULTS.md",
    "docs/FULL_STACK_DETECTION_PROOF.md",
    "docs/ORACLE_FINAL_METRICS_TRUTH.md",
    "docs/GITHUB_REPO_SCOPE_POLICY.md",
}

KEEP_PREFIXES = (
    "oracle_core/",
    "qauthcore/",
    "ethicq/",
    "chronoledger/",
    "ghosttunnel/",
    "oracle_sensor/",
    "mutantshield/",
    "O.R.A.C.L.E_GUi_V1_Figma/",
    "docker/",
)

KEEP_FILES = {
    ".dockerignore",
    ".env.example",
    ".env.docker.example",
    ".gitignore",
    "README.md",
    "RUN_ORACLE_FINAL.md",
    "GITHUB_RELEASE_NOTES_ORACLE_FINAL.md",
    "docker-compose.yml",
    "docker-compose.override.yml",
    "requirements.txt",
    "requirements-oracle-core.txt",
    "requirements-qauthcore.txt",
    "requirements-ethicq.txt",
    "requirements-chronoledger.txt",
    "requirements-ghosttunnel.txt",
}

KEEP_REPORTS = {
    "reports/final/ORACLE_FINAL_CLOSURE_STATUS.md",
    "reports/final/ORACLE_FINAL_CAPABILITY_MATRIX.md",
}

BAD_PREFIXES = (
    "reports/",
    "models_final/",
    "models_candidate/",
    "models_archive/",
    "data/",
    "datasets/",
    "logs/",
    "__pycache__/",
)

BAD_EXTENSIONS = (".pkl", ".pt", ".pth", ".onnx", ".h5", ".joblib", ".csv", ".parquet", ".log")


def git_ls_files() -> List[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def classify(path: str) -> Dict[str, str]:
    lower = path.lower()
    if path in KEEP_FILES or path in ESSENTIAL_DOCS or path in ESSENTIAL_SCRIPT_ALLOWLIST or path in KEEP_REPORTS:
        return {"class": "keep", "reason": "explicit_public_release_allowlist"}
    if path.startswith("docs/assets/screenshots/"):
        return {"class": "remove", "reason": "screenshots_not_required_for_clean_runtime_repo"}
    if path.startswith("scripts/"):
        return {"class": "remove", "reason": "development_or_phase_test_script_not_in_public_allowlist"}
    if path.startswith("reports/"):
        return {"class": "remove", "reason": "local_generated_report_json_or_markdown"}
    if path.startswith(KEEP_PREFIXES):
        return {"class": "keep", "reason": "runtime_or_gui_source"}
    if path.startswith("docs/"):
        return {"class": "remove", "reason": "nonessential_documentation_or_old_submission_note"}
    if lower.endswith(BAD_EXTENSIONS) or path.startswith(BAD_PREFIXES):
        return {"class": "remove", "reason": "data_model_log_or_generated_artifact"}
    return {"class": "review", "reason": "not_matched_by_policy"}


def write_policy(report: Dict[str, Any]) -> None:
    POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GitHub Repository Scope Policy",
        "",
        "The public ORACLE repository is scoped as a professional runtime framework, not a local research scratchpad.",
        "",
        "## Keep",
        "- Runtime source for Oracle Core, QAuthCore, EthicQ, ChronoLedger, GhostTunnel, Oracle Sensor, MutantShield, and the GUI.",
        "- Deployment files, Docker files, requirements, README, and core operator scripts.",
        "- Professional docs for architecture, deployment, usage, security, testing, capabilities, retraining, roadmap, GUI demo, and final metrics truth.",
        "",
        "## Do Not Track",
        "- Raw datasets, model binaries, candidate model artifacts, local logs, caches, generated CSV/parquet files, and private eval outputs.",
        "- Phase scripts, temporary benchmarks, raw JSON reports, and old experimental notes unless they are explicitly part of the final runtime workflow.",
        "",
        "## Latest Audit",
        f"- Generated at: `{report.get('generated_at')}`",
        f"- Tracked files audited: `{report.get('tracked_count')}`",
        f"- Recommended removals: `{len(report.get('remove_from_tracking', []))}`",
        "",
        "Files removed from tracking are not deleted locally; cleanup uses `git rm --cached` only.",
    ]
    POLICY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(apply: bool = False) -> Dict[str, Any]:
    tracked = git_ls_files()
    classified = {path: classify(path) for path in tracked}
    remove = [path for path, item in classified.items() if item["class"] == "remove"]
    review = [path for path, item in classified.items() if item["class"] == "review"]
    applied: Dict[str, Any] = {"applied": False}
    if apply and remove:
        proc = subprocess.run(["git", "rm", "--cached", "--", *remove], cwd=ROOT, text=True, capture_output=True)
        applied = {"applied": True, "exit_code": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-4000:]}
    report: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tracked_count": len(tracked),
        "classification": classified,
        "keep_count": sum(1 for item in classified.values() if item["class"] == "keep"),
        "review_count": len(review),
        "remove_count": len(remove),
        "remove_from_tracking": remove,
        "manual_review": review,
        "apply": applied,
        "pass": len(review) == 0,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "github_repo_scope_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_policy(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Run git rm --cached for files classified as remove.")
    args = parser.parse_args()
    report = run(apply=args.apply)
    print("=== ORACLE GITHUB REPO SCOPE AUDIT ===")
    print(f"Tracked files: {report['tracked_count']}")
    print(f"Keep: {report['keep_count']}")
    print(f"Remove from tracking: {report['remove_count']}")
    print(f"Manual review: {report['review_count']}")
    print(f"Applied cleanup: {report['apply'].get('applied')}")
    print(f"Final Status: {'PASS' if report['pass'] else 'REVIEW'}")
    print(f"Report: {REPORT_DIR / 'github_repo_scope_audit.json'}")
    print(f"Policy: {POLICY_PATH}")


if __name__ == "__main__":
    main()
