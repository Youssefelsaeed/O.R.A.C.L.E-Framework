"""Phase 12.17 backend endpoint coverage test."""
from __future__ import annotations

import time
from typing import Any, Dict

from oracle_phase12_17_common import CORE, QAUTH, ETHICQ, CHRONO, GHOST, sample_payload, timed_request, write_report


def _mark(check: Dict[str, Any], *, expect_4xx: bool = False) -> Dict[str, Any]:
    code = check.get("status_code")
    if expect_4xx:
        check["pass"] = isinstance(code, int) and 400 <= code < 500
    else:
        check["pass"] = bool(check.get("success")) and isinstance(code, int) and code < 400
    return check


def run() -> Dict[str, Any]:
    valid_payload = sample_payload("high_attack", 1)
    malformed_payload = {"flow_id": "bad-risk", "risk_score": {"bad": "type"}, "risk_label": "HIGH"}
    oversized_payload = {**sample_payload("high_attack", 2), "notes": "x" * 200_000}

    checks: Dict[str, Dict[str, Any]] = {}
    checks["oracle_health"] = _mark(timed_request("GET", f"{CORE}/health", timeout=10))
    checks["oracle_docs"] = _mark(timed_request("GET", f"{CORE}/docs", timeout=10))
    checks["oracle_test"] = _mark(timed_request("GET", f"{CORE}/oracle/test", timeout=10))
    checks["oracle_process_valid"] = _mark(timed_request("POST", f"{CORE}/oracle/process", json_body=valid_payload, timeout=30))
    checks["oracle_process_malformed"] = _mark(timed_request("POST", f"{CORE}/oracle/process", json_body=malformed_payload, timeout=30), expect_4xx=True)
    oversized = timed_request("POST", f"{CORE}/oracle/process", json_body=oversized_payload, timeout=30)
    oversized["pass"] = isinstance(oversized.get("status_code"), int) and oversized["status_code"] in {200, 207, 413, 422}
    checks["oracle_process_oversized_safe"] = oversized
    for name, method, path, timeout in [
        ("dashboard_summary", "GET", "/oracle/dashboard/summary", 10),
        ("dashboard_latest_events", "GET", "/oracle/dashboard/latest-events", 10),
        ("dashboard_health", "GET", "/oracle/dashboard/health", 10),
        ("dashboard_performance", "GET", "/oracle/dashboard/performance", 10),
        ("dashboard_evolution", "GET", "/oracle/dashboard/evolution", 10),
        ("dashboard_reports", "GET", "/oracle/dashboard/reports", 10),
        ("action_health_check", "POST", "/oracle/dashboard/actions/health-check", 30),
        ("action_backend_validation", "POST", "/oracle/dashboard/actions/backend-validation", 60),
        ("action_evolution_dry_run", "POST", "/oracle/dashboard/actions/evolution-dry-run", 360),
        ("action_qauth_test_token", "POST", "/oracle/dashboard/actions/qauth-test-token", 30),
        ("action_ghosttunnel_test_transmit", "POST", "/oracle/dashboard/actions/ghosttunnel-test-transmit", 30),
        ("action_chronoledger_chain_verify", "POST", "/oracle/dashboard/actions/chronoledger-chain-verify", 30),
    ]:
        checks[name] = _mark(timed_request(method, f"{CORE}{path}", timeout=timeout))

    qauth_token = timed_request(
        "POST",
        f"{QAUTH}/api/v1/tokens/generate",
        json_body={"metadata": {"source_module": "phase12_17"}, "flow_id": "phase12-17-qauth"},
        timeout=30,
    )
    checks["qauth_token_generate"] = _mark(qauth_token)
    token = qauth_token.get("body_summary", {}).get("token") or None
    checks["qauth_health"] = _mark(timed_request("GET", f"{QAUTH}/api/v1/health", timeout=10)) if timed_request("GET", f"{QAUTH}/api/v1/health", timeout=10).get("status_code") != 404 else _mark(timed_request("GET", f"{QAUTH}/docs", timeout=10))
    verify_body = {"token": token or "missing", "timestamp": time.time(), "flow_id": "phase12-17-qauth"}
    checks["qauth_token_verify"] = _mark(timed_request("POST", f"{QAUTH}/api/v1/tokens/verify", json_body=verify_body, timeout=30))

    checks["ethicq_health"] = _mark(timed_request("GET", f"{ETHICQ}/api/v1/health", timeout=10)) if timed_request("GET", f"{ETHICQ}/api/v1/health", timeout=10).get("status_code") != 404 else _mark(timed_request("GET", f"{ETHICQ}/docs", timeout=10))
    checks["ethicq_decision"] = _mark(
        timed_request(
            "POST",
            f"{ETHICQ}/api/v1/decisions/evaluate",
            json_body={
                "threat_alert": {"target_ip": "198.51.100.4", "source_ip": "192.0.2.4", "risk_score": 0.9, "risk_label": "HIGH"},
                "qauthcore_token": token or "test",
                "auth_context": {"verified": True, "trust_level": "high"},
            },
            timeout=30,
        )
    )

    checks["chronoledger_health"] = _mark(timed_request("GET", f"{CHRONO}/health", timeout=10))
    checks["chronoledger_event_append"] = _mark(
        timed_request(
            "POST",
            f"{CHRONO}/api/v1/events",
            json_body={"event_type": "phase12_17_test", "data": {"trace_id": "phase12-17"}, "source_module": "phase12_17", "qauthcore_token": token or "test", "qauthcore_timestamp": time.time()},
            timeout=30,
        )
    )
    checks["chronoledger_chain_verify"] = _mark(timed_request("GET", f"{CHRONO}/chain/verify", timeout=30))

    ghost_health = timed_request("GET", f"{GHOST}/health", timeout=10)
    checks["ghosttunnel_health"] = _mark(ghost_health) if ghost_health.get("status_code") != 404 else _mark(timed_request("GET", f"{GHOST}/docs", timeout=10))
    checks["ghosttunnel_transmit"] = _mark(
        timed_request(
            "POST",
            f"{GHOST}/api/v1/transmit",
            json_body={"data": {"trace_id": "phase12-17", "flow_id": "phase12-17"}, "priority": "normal", "preferred_protocol": "http", "metadata": {"source": "phase12_17"}},
            timeout=30,
        )
    )

    report = {
        "generated_at": time.time(),
        "checks": checks,
        "total": len(checks),
        "passed": sum(1 for check in checks.values() if check.get("pass")),
    }
    report["pass"] = report["passed"] == report["total"]
    path = write_report("phase12_17_backend_endpoint_test.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    print("\n=== ORACLE PHASE 12.17 BACKEND ENDPOINT TEST ===")
    for name, check in report["checks"].items():
        print(f"{name}: {'PASS' if check.get('pass') else 'FAIL'} ({check.get('status_code')}) {check.get('latency_ms')}ms")
    print(f"Passed: {report['passed']}/{report['total']}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
