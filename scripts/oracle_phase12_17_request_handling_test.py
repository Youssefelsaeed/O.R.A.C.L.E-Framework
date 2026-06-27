"""Phase 12.17 Oracle Core request handling and load verification."""
from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import requests

from oracle_phase12_17_common import CORE, sample_payload, timed_request, write_report

TOTAL_REQUESTS = 1000
CONCURRENCY_LEVELS = [1, 5, 10, 25]
REQUESTS_PER_LEVEL = {1: 850, 5: 100, 10: 30, 25: 20}


def _payload_for(idx: int) -> tuple[str, Dict[str, Any]]:
    mod = idx % 20
    if mod in {0, 1}:
        return "malformed", {"flow_id": f"malformed-{idx}", "risk_score": {"bad": "type"}, "risk_label": "HIGH"}
    if mod == 2:
        payload = sample_payload("high_attack", idx)
        payload["notes"] = "x" * 200_000
        return "oversized", payload
    if mod in {3, 4, 5, 6}:
        return "benign", sample_payload("benign", idx)
    if mod in {7, 8, 9, 10}:
        return "medium", sample_payload("medium", idx)
    if mod in {11, 12, 13, 14}:
        return "dohbrw", sample_payload("dohbrw", idx)
    return "high_attack", sample_payload("high_attack", idx)


def _send(idx: int) -> Dict[str, Any]:
    kind, payload = _payload_for(idx)
    started = time.perf_counter()
    try:
        response = requests.post(f"{CORE}/oracle/process", json=payload, timeout=30)
        latency = (time.perf_counter() - started) * 1000
        try:
            body = response.json()
        except Exception:
            body = {}
        return {
            "kind": kind,
            "status_code": response.status_code,
            "latency_ms": round(latency, 2),
            "server_latency_ms": ((body.get("pipeline_timings_ms") or {}).get("total_ms") if isinstance(body, dict) else None),
            "oracle_trace_id": body.get("oracle_trace_id"),
            "audit_logged": bool((body.get("audit") or {}).get("logged")),
            "failed_services": body.get("failed_services", []),
            "rejected_reason": body.get("reason"),
        }
    except Exception as exc:
        return {"kind": kind, "status_code": None, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": str(exc), "failed_services": ["request_exception"]}


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round((pct / 100.0) * (len(ordered) - 1))))
    return round(ordered[idx], 2)


def run() -> Dict[str, Any]:
    started = time.time()
    results: List[Dict[str, Any]] = []
    per_level: Dict[str, Any] = {}
    current = 0
    for concurrency in CONCURRENCY_LEVELS:
        per_level_count = REQUESTS_PER_LEVEL[concurrency]
        level_started = time.time()
        level_results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(_send, idx) for idx in range(current, current + per_level_count)]
            for future in as_completed(futures):
                item = future.result()
                level_results.append(item)
                results.append(item)
        current += per_level_count
        per_level[str(concurrency)] = {
            "requests": len(level_results),
            "duration_seconds": round(time.time() - level_started, 2),
            "avg_latency_ms": round(statistics.mean([r["latency_ms"] for r in level_results]), 2) if level_results else 0,
            "p95_latency_ms": _percentile([r["latency_ms"] for r in level_results], 95),
        }

    valid = [r for r in results if r["kind"] not in {"malformed", "oversized"}]
    malformed = [r for r in results if r["kind"] == "malformed"]
    oversized = [r for r in results if r["kind"] == "oversized"]
    valid_success = [r for r in valid if r.get("status_code") == 200]
    valid_degraded = [r for r in valid if r.get("status_code") == 207]
    valid_failed = [r for r in valid if r.get("status_code") not in {200, 207}]
    clean_rejections = [r for r in malformed + oversized if isinstance(r.get("status_code"), int) and 400 <= r["status_code"] < 500]
    latencies = [float(r["latency_ms"]) for r in results]
    audit_logged = [r for r in valid if r.get("audit_logged")]
    failed_services: Dict[str, int] = {}
    for row in valid:
        for service in row.get("failed_services") or []:
            failed_services[service] = failed_services.get(service, 0) + 1

    summary = timed_request("GET", f"{CORE}/oracle/dashboard/summary", timeout=20)
    assurance = ((summary.get("body_summary") or {}).get("assurance") or {}) if False else {}
    raw_summary = requests.get(f"{CORE}/oracle/dashboard/summary", timeout=20).json()
    assurance = raw_summary.get("assurance") or {}
    ghost = raw_summary.get("ghosttunnel") or {}

    duration = time.time() - started
    metrics = {
        "total": len(results),
        "valid_total": len(valid),
        "valid_success": len(valid_success),
        "valid_degraded": len(valid_degraded),
        "valid_failed": len(valid_failed),
        "malformed_rejected_4xx": len([r for r in malformed if isinstance(r.get("status_code"), int) and 400 <= r["status_code"] < 500]),
        "oversized_rejected_4xx": len([r for r in oversized if isinstance(r.get("status_code"), int) and 400 <= r["status_code"] < 500]),
        "client_avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "client_p95_latency_ms": _percentile(latencies, 95),
        "client_p99_latency_ms": _percentile(latencies, 99),
        "client_max_latency_ms": round(max(latencies), 2) if latencies else 0,
        "throughput_events_per_sec": round(len(results) / duration, 2) if duration else 0,
        "retries": 0,
        "failed_services": failed_services,
        "audit_logged_rate": round(len(audit_logged) / max(1, len(valid)), 4),
        "assurance_latest_pending": assurance.get("latest_pending"),
        "assurance_latest_failed": assurance.get("latest_failed"),
        "ghost_jobs_pending": ghost.get("jobs_pending"),
        "ghost_jobs_failed": ghost.get("jobs_failed"),
    }
    server_latencies = [
        float(r["server_latency_ms"])
        for r in valid
        if isinstance(r.get("server_latency_ms"), (int, float))
    ]
    metrics.update(
        {
            "avg_latency_ms": round(statistics.mean(server_latencies), 2) if server_latencies else metrics["client_avg_latency_ms"],
            "p95_latency_ms": _percentile(server_latencies, 95) if server_latencies else metrics["client_p95_latency_ms"],
            "p99_latency_ms": _percentile(server_latencies, 99) if server_latencies else metrics["client_p99_latency_ms"],
            "max_latency_ms": round(max(server_latencies), 2) if server_latencies else metrics["client_max_latency_ms"],
            "latency_basis": "oracle_pipeline_timings_ms",
        }
    )
    pass_checks = {
        "valid_failed_zero": metrics["valid_failed"] == 0,
        "degraded_under_or_equal_1pct": (metrics["valid_degraded"] / max(1, metrics["valid_total"])) <= 0.01,
        "malformed_rejected_cleanly": metrics["malformed_rejected_4xx"] == len(malformed),
        "oversized_rejected_cleanly": metrics["oversized_rejected_4xx"] == len(oversized),
        "p95_under_1000_ms": metrics["p95_latency_ms"] <= 1000,
        "audit_logged_at_least_99pct": metrics["audit_logged_rate"] >= 0.99,
        "assurance_pending_zero": metrics["assurance_latest_pending"] == 0,
        "ghost_failed_zero": (metrics["ghost_jobs_failed"] or 0) == 0,
    }
    report = {
        "generated_at": time.time(),
        "concurrency_levels": CONCURRENCY_LEVELS,
        "requests_per_level": REQUESTS_PER_LEVEL,
        "per_level": per_level,
        "metrics": metrics,
        "pass_checks": pass_checks,
        "sample_failures": [r for r in results if r.get("status_code") not in {200, 207, 413, 422}][:20],
        "duration_seconds": round(duration, 2),
    }
    report["pass"] = all(pass_checks.values())
    path = write_report("phase12_17_request_handling_test.json", report)
    report["report_path"] = str(path)
    return report


def main() -> None:
    report = run()
    metrics = report["metrics"]
    print("\n=== ORACLE PHASE 12.17 REQUEST HANDLING TEST ===")
    print(f"Total: {metrics['total']}")
    print(f"Valid Success: {metrics['valid_success']}")
    print(f"Valid Degraded: {metrics['valid_degraded']}")
    print(f"Valid Failed: {metrics['valid_failed']}")
    print(f"Malformed Rejected 4xx: {metrics['malformed_rejected_4xx']}")
    print(f"Oversized Rejected 4xx: {metrics['oversized_rejected_4xx']}")
    print(f"Avg/P95/P99/Max Latency ms ({metrics['latency_basis']}): {metrics['avg_latency_ms']} / {metrics['p95_latency_ms']} / {metrics['p99_latency_ms']} / {metrics['max_latency_ms']}")
    print(f"Client P95 Latency ms: {metrics['client_p95_latency_ms']}")
    print(f"Throughput events/sec: {metrics['throughput_events_per_sec']}")
    print(f"Audit Logged Rate: {metrics['audit_logged_rate']}")
    for name, ok in report["pass_checks"].items():
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
    print(f"Final Status: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {report['report_path']}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
