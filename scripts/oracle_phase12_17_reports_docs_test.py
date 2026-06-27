"""Phase 12.17 reports and documentation availability test."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from oracle_phase12_17_common import CORE, ROOT, timed_request, write_report


def _exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _glob_any(pattern: str) -> bool:
    return any(ROOT.glob(pattern))


def run() -> Dict[str, Any]:
    docs = {
        "README.md": _exists("README.md"),
        "Docker docs": _exists("docs/DOCKER_DEPLOYMENT_ARCHITECTURE.md"),
        "Deployment docs": _exists("docs/DEPLOYMENT.md"),
        "Manual validation guide": _exists("docs/FINAL_MANUAL_VALIDATION_GUIDE.md"),
        "SIEM/SOAR/EDR future doc": _exists("docs/SIEM_SOAR_EDR_INTEGRATION.md"),
        "GUI data source docs": _exists("docs/GUI_DATA_SOURCES.md"),
        "GitHub release notes": _exists("GITHUB_RELEASE_NOTES_ORACLE_FINAL.md"),
        "Run guide": _exists("RUN_ORACLE_FINAL.md"),
    }
    reports = {
        "module capability reports": _glob_any("reports/final/*module*capability*.json") or _exists("reports/final/oracle_phase12_11_module_capability_validation.json"),
        "final benchmark reports": _glob_any("reports/final/*benchmark*.json") or _glob_any("reports/final/*final*evaluation*.json"),
        "final QA reports": _glob_any("reports/final/*qa*.json") or _glob_any("reports/final/*rationality*.json"),
        "operator reports": _exists("reports/final/module_gui_actions_report.json"),
        "docker safety report": _exists("reports/final/docker_packaging_safety_report.json"),
        "screenshot folder": _exists("docs/assets/screenshots") or _exists("docs/assets"),
    }
    endpoint_checks = {
        "reports_list": timed_request("GET", f"{CORE}/oracle/dashboard/reports", timeout=10),
        "backend_validation_report": timed_request("GET", f"{CORE}/oracle/dashboard/reports/backend_validation", timeout=10),
        "evolution_run_report": timed_request("GET", f"{CORE}/oracle/dashboard/reports/evolution_run", timeout=10),
        "chronoledger_evidence_report": timed_request("GET", f"{CORE}/oracle/dashboard/reports/chronoledger_evidence", timeout=10),
    }
    for item in endpoint_checks.values():
        item["pass"] = bool(item.get("success")) and isinstance(item.get("status_code"), int) and item["status_code"] < 500
    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "docs": docs,
        "reports": reports,
        "endpoint_checks": endpoint_checks,
    }
    report["pass"] = all(docs.values()) and all(reports.values()) and all(item.get("pass") for item in endpoint_checks.values())
    path = write_report("phase12_17_reports_docs_test.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.17 REPORTS & DOCS TEST ===")
    print(f"Docs: {'PASS' if all(report['docs'].values()) else 'FAIL'}")
    print(f"Reports: {'PASS' if all(report['reports'].values()) else 'FAIL'}")
    print(f"Report Endpoints: {'PASS' if all(item.get('pass') for item in report['endpoint_checks'].values()) else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
