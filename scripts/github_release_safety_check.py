"""Production GitHub release safety check for O.R.A.C.L.E Framework."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "final"
REPORT_JSON = REPORT_DIR / "github_release_safety_check.json"
REPORT_MD = REPORT_DIR / "github_release_safety_check.md"
MODELS_FINAL = ROOT / "Mutant_Sheild Module" / "mutantshield" / "src" / "FinalVersion" / "models_final"

PROFESSIONAL_DOCS = [
    "docs/ARCHITECTURE.md",
    "docs/DEPLOYMENT.md",
    "docs/USER_GUIDE.md",
    "docs/SECURITY_MODEL.md",
    "docs/TESTING_AND_VALIDATION.md",
    "docs/MODULE_CAPABILITIES.md",
    "docs/RETRAINING_AND_EVOLUTION.md",
    "docs/API_REFERENCE.md",
    "docs/DATASETS.md",
    "docs/ROADMAP.md",
    "docs/CONTRIBUTING.md",
    "docs/GITHUB_UPLOAD_GUIDE.md",
    "docs/REPOSITORY_STRUCTURE.md",
]

FORBIDDEN_STAGE_RE = re.compile(
    r"(^|/)(Workin with|node_modules|\.venv|venv|__pycache__|reports|Diagrams)(/|$)|"
    r"(^|/)\.env$|"
    r"\.(pkl|joblib|pth|pt|onnx|keras|h5|pcap|pcapng|parquet|feather|arff|zip|7z|tar|gz)$|"
    r"(^|/)scripts/(test_|oracle_phase|phase|train_|build_|analyze_|benchmark_|profile_).+\.py$",
    re.IGNORECASE,
)
SECRET_RE = re.compile(
    r"(?i)^\s*([A-Z0-9_]*(?:API[_-]?KEY|SECRET|PASSWORD|PRIVATE[_-]?KEY|ACCESS[_-]?TOKEN)[A-Z0-9_]*)\s*=\s*['\"]([^'\"]{16,})['\"]"
)
ALLOWLIST_SECRET_MARKERS = ("example", "placeholder", "your-secret", "default", "dev_token", "test_token")
SKIP_DIRS = {
    ".git",
    ".cursor",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "Workin with",
    "reports",
    "Diagrams",
    "data",
    "keys",
    "models_registry",
    "modules",
    "Chrono_Ledger Module",
    "Ethic-Q Module",
    "Ghost_Tunnel Module",
    "Mutant_Sheild Module",
    "Q-AuthCore Module",
    "O.R.A.C.L.E",
}
TEXT_EXTS = {".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".env", ".example", ".ts", ".tsx", ".js", ".css", ".html"}
RELEASE_SCRIPT_NAMES = {
    "start_oracle_stack.py",
    "oracle_stack_common.py",
    "check_services_health.py",
    "github_release_safety_check.py",
    "check_all_services.py",
    "phase8_common.py",
    "oracle_runtime_mode.py",
    "oracle_final_acceptance_test.py",
    "oracle_phase11_final_benchmark.py",
    "oracle_phase12_11_module_capability_validation.py",
    "oracle_post_packaging_final_regression.py",
    "test_gui_live_status.py",
    "test_gui_buttons_live_actions.py",
    "test_dashboard_action_endpoints.py",
    "test_gui_operator_console_live.py",
    "oracle_live_sensor_smoke_test.py",
    "oracle_realtime_replay_proof.py",
    "oracle_operator_final_validation.py",
    "test_mutantshield_detection_capability.py",
    "test_qauthcore_authentication_capability.py",
    "test_chronoledger_logging_capability.py",
    "test_ghosttunnel_communication_capability.py",
}
ALLOWED_STAGED_REPORTS = {
    "reports/final/operator_runtime_safety_report.json",
    "reports/final/gui_live_actions_report.json",
    "reports/final/gui_data_source_map.json",
    "reports/final/oracle_live_sensor_proof_report.json",
    "reports/final/oracle_realtime_replay_proof_report.json",
    "reports/final/gui_live_monitor_report.json",
    "reports/final/oracle_operator_final_validation_report.json",
    "reports/final/dashboard_action_endpoints_report.json",
    "reports/final/gui_operator_console_live_report.json",
    "reports/final/ORACLE_FINAL_CLOSURE_STATUS.json",
    "reports/final/ORACLE_FINAL_CLOSURE_STATUS.md",
}
RELEASE_ROOT_FILES = {
    "README.md",
    "RUN_ORACLE_FINAL.md",
    "GITHUB_RELEASE_NOTES_ORACLE_FINAL.md",
    ".gitignore",
    ".env.example",
    "requirements.txt",
}
RELEASE_PREFIXES = {
    "docs",
    "oracle_core",
    "oracle_sensor",
    "mutantshield",
    "qauthcore",
    "ethicq",
    "chronoledger",
    "ghosttunnel",
    "O.R.A.C.L.E_GUi_V1_Figma",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _walk_release_files() -> Iterable[Path]:
    for current, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = Path(current) / name
            rel = path.relative_to(ROOT).as_posix()
            top = rel.split("/", 1)[0]
            if rel in RELEASE_ROOT_FILES:
                yield path
            elif top == "scripts" and name in RELEASE_SCRIPT_NAMES:
                yield path
            elif top in RELEASE_PREFIXES:
                yield path


def _models_hash() -> Dict[str, str]:
    if not MODELS_FINAL.exists():
        return {}
    hashes: Dict[str, str] = {}
    for path in MODELS_FINAL.rglob("*"):
        if path.is_file():
            hashes[str(path.relative_to(MODELS_FINAL))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _git_staged_files() -> List[str]:
    result = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def _secret_findings() -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for path in _walk_release_files():
        if path.suffix.lower() not in TEXT_EXTS and not path.name.endswith(".env.example"):
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            match = SECRET_RE.search(line)
            if not match:
                continue
            lowered = line.lower()
            if any(marker in lowered for marker in ALLOWLIST_SECRET_MARKERS):
                continue
            findings.append({"path": rel, "line": line_no, "variable": match.group(1)})
    return findings


def _large_files() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in _walk_release_files():
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size >= 10 * 1024 * 1024:
            rows.append({"path": path.relative_to(ROOT).as_posix(), "size_mb": round(size / (1024 * 1024), 2)})
    return sorted(rows, key=lambda row: row["size_mb"], reverse=True)


def run() -> Dict[str, Any]:
    before = _models_hash()
    gitignore = _read(ROOT / ".gitignore")
    staged = _git_staged_files()
    forbidden_staged = [
        path
        for path in staged
        if FORBIDDEN_STAGE_RE.search(path)
        and path not in ALLOWED_STAGED_REPORTS
        and not (path.startswith("scripts/") and Path(path).name in RELEASE_SCRIPT_NAMES)
    ]
    docs = {doc: (ROOT / doc).exists() for doc in PROFESSIONAL_DOCS}
    checks = {
        "raw datasets ignored": "Workin with/" in gitignore and "*.pcap" in gitignore,
        ".env ignored": ".env" in gitignore and "!.env.example" in gitignore,
        "node_modules ignored": "node_modules/" in gitignore,
        "venv ignored": ".venv/" in gitignore and "venv/" in gitignore,
        "cache ignored": "__pycache__/" in gitignore and ".pytest_cache/" in gitignore,
        "models_final handling documented": "models_final" in _read(ROOT / "README.md") and "Git LFS" in _read(ROOT / "README.md"),
        "reports not staged": not any(path.startswith("reports/") and path not in ALLOWED_STAGED_REPORTS for path in staged),
        "README exists": (ROOT / "README.md").exists(),
        "professional docs exist": all(docs.values()),
        "secrets not found": not _secret_findings(),
        "forbidden staged files absent": not forbidden_staged,
    }
    report = {
        "generated_at": time.time(),
        "repository": "O.R.A.C.L.E-Framework",
        "checks": checks,
        "professional_docs": docs,
        "secret_findings": _secret_findings(),
        "large_files": _large_files(),
        "staged_file_count": len(staged),
        "forbidden_staged_files": forbidden_staged,
        "models_final_unchanged": before == _models_hash() and bool(before),
        "pass": all(checks.values()) and before == _models_hash() and bool(before),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(
        "\n".join(
            [
                "# GitHub Release Safety Check",
                "",
                f"Repository: `O.R.A.C.L.E-Framework`",
                f"Safety Check: **{'PASS' if report['pass'] else 'FAIL'}**",
                f"models_final unchanged: **{str(report['models_final_unchanged']).upper()}**",
                "",
                "## Checks",
                "",
                *[f"- {name}: {'PASS' if ok else 'FAIL'}" for name, ok in checks.items()],
                "",
                f"Large files listed: {len(report['large_files'])}",
                f"Forbidden staged files: {len(forbidden_staged)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> None:
    report = run()
    print("=== O.R.A.C.L.E FRAMEWORK RELEASE SAFETY CHECK ===")
    print(f"Safety Check: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Professional Docs: {'PASS' if report['checks']['professional docs exist'] else 'FAIL'}")
    print(f"Reports Not Staged: {'PASS' if report['checks']['reports not staged'] else 'FAIL'}")
    print(f"models_final unchanged: {str(report['models_final_unchanged']).upper()}")
    print(f"Report: {REPORT_JSON}")
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
