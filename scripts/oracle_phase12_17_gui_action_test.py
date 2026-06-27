"""Phase 12.17 GUI operator action verification."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from oracle_phase12_17_common import CORE, GUI, ROOT, timed_request, write_report

COMPONENTS = ROOT / "O.R.A.C.L.E_GUi_V1_Figma" / "src" / "app" / "components"
DIST_INDEX = ROOT / "O.R.A.C.L.E_GUi_V1_Figma" / "dist" / "index.html"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def run() -> Dict[str, Any]:
    dashboard = _read(COMPONENTS / "global-dashboard.tsx")
    mutant = _read(COMPONENTS / "mutant-shield.tsx")
    lifecycle = _read(COMPONENTS / "ai-lifecycle.tsx")
    qauth = _read(COMPONENTS / "qauth-core.tsx")
    ethicq = _read(COMPONENTS / "ethic-q.tsx")
    ghost = _read(COMPONENTS / "ghost-tunnel.tsx")
    chrono = _read(COMPONENTS / "chrono-ledger.tsx")
    settings = _read(COMPONENTS / "settings-page.tsx")

    source_checks = {
        "api_base_shown": "API Base" in dashboard or "API base" in dashboard,
        "data_mode_live_connected": "LIVE BACKEND CONNECTED" in dashboard,
        "refresh_action_handler": "refreshAll" in dashboard,
        "health_check_action_handler": "runHealthCheck" in dashboard,
        "backend_validation_action_handler": "runBackendValidation" in dashboard,
        "latest_events_widget": "Latest ORACLE Events" in dashboard,
        "live_proof_panel": "Live Processing Proof" in dashboard,
        "mutantshield_dry_run_handler": "runEvolutionDryRun" in mutant,
        "mutantshield_retraining_locked": "Production retraining is blocked" in mutant,
        "evolution_dry_run_handler": "runEvolutionDryRun" in lifecycle,
        "promote_candidate_locked": "Production models remain unchanged" in lifecycle or "promotion" in lifecycle.lower(),
        "qauth_manage_users_locked": "QAuthCore user management is a future admin feature" in qauth,
        "qauth_test_token_action": "runQAuthTestToken" in qauth,
        "ethicq_edit_rules_locked": "EthicQ rule editing is locked" in ethicq,
        "ghosttunnel_demo_transmit": "runGhostTunnelTestTransmit" in ghost,
        "chronoledger_chain_verify": "runChronoLedgerChainVerify" in chrono,
        "settings_dangerous_controls_locked": "SAFETY_BLOCKED_MSG" in settings and "showLocked" in settings,
    }

    endpoint_checks = {
        "gui_reachable": timed_request("GET", GUI, timeout=10),
        "dashboard_summary": timed_request("GET", f"{CORE}/oracle/dashboard/summary", timeout=10),
        "latest_events": timed_request("GET", f"{CORE}/oracle/dashboard/latest-events", timeout=10),
        "health_check_action": timed_request("POST", f"{CORE}/oracle/dashboard/actions/health-check", timeout=30),
        "backend_validation_action": timed_request("POST", f"{CORE}/oracle/dashboard/actions/backend-validation", timeout=60),
        "evolution_dry_run_action": timed_request("POST", f"{CORE}/oracle/dashboard/actions/evolution-dry-run", timeout=360),
        "qauth_test_token_action": timed_request("POST", f"{CORE}/oracle/dashboard/actions/qauth-test-token", timeout=30),
        "ghosttunnel_test_transmit_action": timed_request("POST", f"{CORE}/oracle/dashboard/actions/ghosttunnel-test-transmit", timeout=30),
        "chronoledger_chain_verify_action": timed_request("POST", f"{CORE}/oracle/dashboard/actions/chronoledger-chain-verify", timeout=30),
        "reports_list": timed_request("GET", f"{CORE}/oracle/dashboard/reports", timeout=10),
    }
    for check in endpoint_checks.values():
        check["pass"] = bool(check.get("success")) and isinstance(check.get("status_code"), int) and check["status_code"] < 400

    report = {
        "generated_at": time.time(),
        "browser_automation": "not_used",
        "limitation": "Validated by source inspection, live backend action endpoints, and GUI HTTP reachability.",
        "gui_build_asset_present": DIST_INDEX.exists(),
        "source_checks": source_checks,
        "endpoint_checks": endpoint_checks,
    }
    report["pass"] = all(source_checks.values()) and all(check.get("pass") for check in endpoint_checks.values())
    path = write_report("phase12_17_gui_action_test.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.17 GUI ACTION TEST ===")
    print(f"GUI Reachable: {'PASS' if report['endpoint_checks']['gui_reachable'].get('pass') else 'FAIL'}")
    print(f"Dashboard Source Actions: {'PASS' if all(report['source_checks'].values()) else 'FAIL'}")
    print(f"Backend Action Endpoints: {'PASS' if all(c.get('pass') for c in report['endpoint_checks'].values()) else 'FAIL'}")
    print(f"Browser Automation: {report['browser_automation']}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
