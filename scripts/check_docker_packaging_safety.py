"""Safety audit for ORACLE Docker runtime packaging."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "final" / "docker_packaging_safety_report.json"

FORBIDDEN_CONTEXT_MARKERS = [
    "Workin with",
    "*.pcap",
    "*.pcapng",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    "reports",
    "models_final",
    "models_candidate",
    "*.pkl",
    "*.joblib",
    "*.pth",
    "*.pt",
    "*.onnx",
    "*.keras",
    "*.h5",
]
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?im)^\s*[A-Z0-9_]*(?:SECRET|PASSWORD|TOKEN|API[_-]?KEY|PRIVATE[_-]?KEY)[A-Z0-9_]*\s*=\s*['\"]?[^#\n]{12,}"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _dockerfiles() -> List[str]:
    return sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in (ROOT / "docker").glob("*/Dockerfile"))


def run() -> Dict[str, Any]:
    dockerignore = _read(ROOT / ".dockerignore")
    compose = _read(ROOT / "docker-compose.yml")
    override = _read(ROOT / "docker-compose.override.yml")
    env_example = _read(ROOT / ".env.docker.example")
    compose_all = compose + "\n" + override
    dockerignore_checks = {
        marker: marker in dockerignore for marker in FORBIDDEN_CONTEXT_MARKERS
    }
    checks = {
        "dockerignore_exists": (ROOT / ".dockerignore").exists(),
        "compose_exists": (ROOT / "docker-compose.yml").exists(),
        "all_runtime_dockerfiles_exist": len(_dockerfiles()) == 6,
        "datasets_excluded_from_context": all(dockerignore_checks.get(m, False) for m in ["Workin with", "*.pcap", "*.pcapng"]),
        "env_files_excluded": ".env" in dockerignore and "!.env.docker.example" in dockerignore,
        "node_modules_excluded": "node_modules" in dockerignore,
        "model_binaries_excluded": all(dockerignore_checks.get(m, False) for m in ["*.pkl", "*.joblib", "*.pth", "*.pt", "*.onnx", "*.keras", "*.h5"]),
        "models_final_mounted_read_only": "./models_final:/app/models_final:ro" in compose_all,
        "models_candidate_mounted_read_write": "./models_candidate:/app/models_candidate" in compose_all,
        "reports_and_data_mounted": "./reports:/app/reports" in compose_all and "./data:/app/data" in compose_all,
        "compose_has_no_secret_assignments": not SECRET_ASSIGNMENT_RE.search(compose_all),
        "env_example_has_no_secret_values": not SECRET_ASSIGNMENT_RE.search(env_example),
        "model_handling_documented": "models_final" in _read(ROOT / "docs" / "DOCKER_DEPLOYMENT_ARCHITECTURE.md"),
    }
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "dockerfiles": _dockerfiles(),
        "dockerignore_checks": dockerignore_checks,
        "checks": checks,
        "pass": all(checks.values()),
        "models_final_policy": "mounted_read_only_not_baked",
        "raw_datasets_policy": "excluded_from_image_context",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE DOCKER PACKAGING SAFETY ===")
    for name, ok in report["checks"].items():
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {REPORT}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
