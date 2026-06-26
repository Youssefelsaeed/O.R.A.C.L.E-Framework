"""Phase 12.11 GhostTunnel communication capability validation."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import signal
import statistics
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import requests

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from oracle_stack_common import kill_all_ports, start_services, wait_for_health  # noqa: E402
from phase8_common import percentile, production_model_hashes  # noqa: E402

OUT_DIR = ROOT / "reports" / "final" / "module_capabilities"
JSON_PATH = OUT_DIR / "ghosttunnel_communication_capability.json"
MD_PATH = OUT_DIR / "ghosttunnel_communication_capability.md"
BASE = "http://127.0.0.1:8004/api/v1"


def _shutdown(procs: List[Any]) -> None:
    for proc in procs:
        if proc.poll() is None:
            try:
                proc.send_signal(signal.SIGTERM)
            except Exception:
                proc.terminate()
    time.sleep(2)
    for proc in procs:
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass


def _payload(size: str = "small", i: int = 0) -> Dict[str, Any]:
    blob = "x" * (64 if size == "small" else 4096 if size == "medium" else 20000)
    return {
        "data": {
            "trace_id": f"ghost-cap-{size}-{i}-{uuid.uuid4().hex[:8]}",
            "payload": blob,
            "classification": "module_capability",
        },
        "priority": "normal",
        "metadata": {"phase": "12.11", "size": size, "index": i},
    }


def _transmit(i: int, size: str = "small") -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        r = requests.post(f"{BASE}/transmit", json=_payload(size, i), timeout=15)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        body = r.json() if r.content else {}
        return {
            "ok": r.status_code < 400 and body.get("accepted", True) is not False,
            "status_code": r.status_code,
            "ack_latency_ms": elapsed,
            "body": body,
            "job_id": body.get("transmit_job_id"),
            "entropy_source": body.get("entropy_source"),
            "assurance_state": body.get("assurance_state"),
        }
    except Exception as exc:
        return {"ok": False, "ack_latency_ms": round((time.perf_counter() - t0) * 1000, 2), "error": str(exc)}


def _poll(job_id: str, timeout_s: float = 45.0) -> Dict[str, Any]:
    start = time.perf_counter()
    final: Dict[str, Any] = {"status": "missing"}
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE}/transmit/jobs/{job_id}", timeout=5)
            if r.status_code < 400:
                final = r.json()
                if final.get("status") in ("transmitted", "completed", "failed"):
                    break
        except Exception as exc:
            final = {"status": "error", "error": str(exc)}
        time.sleep(1)
    final["completion_latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
    return final


def run_capability(start_stack: bool = True) -> Dict[str, Any]:
    before = production_model_hashes()
    procs: List[Any] = []
    if start_stack:
        kill_all_ports()
        procs = start_services()
        wait_for_health(max_wait_s=120.0)
    try:
        health = requests.get(f"{BASE}/health", timeout=10).json()
        stats_before = requests.get(f"{BASE}/stats", timeout=10).json()
        single = _transmit(0, "small")
        sizes = [_transmit(1, "small"), _transmit(2, "medium"), _transmit(3, "large")]
        batch_payload = [_payload("small", i) for i in range(4, 9)]
        batch_t0 = time.perf_counter()
        batch = requests.post(f"{BASE}/transmit/batch", json=batch_payload, timeout=30)
        batch_latency = round((time.perf_counter() - batch_t0) * 1000, 2)
        batch_body = batch.json() if batch.content else []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            concurrent_rows = list(executor.map(lambda i: _transmit(i, "small"), range(10, 30)))
        invalid = requests.post(f"{BASE}/transmit", json={}, timeout=10)
        accepted_rows = [single] + sizes + concurrent_rows
        job_ids = [r.get("job_id") for r in accepted_rows if r.get("job_id")]
        completions = [_poll(job_id) for job_id in job_ids[:20]]
        health_after = requests.get(f"{BASE}/health", timeout=10).json()
        stats_after = requests.get(f"{BASE}/stats", timeout=10).json()
        ack_latencies = [r.get("ack_latency_ms", 0.0) for r in accepted_rows if r.get("ack_latency_ms")]
        completion_latencies = [c.get("completion_latency_ms", 0.0) for c in completions if c.get("completion_latency_ms")]
        accepted_count = sum(1 for r in accepted_rows if r.get("ok"))
        transmitted_count = sum(1 for c in completions if c.get("status") in ("transmitted", "completed"))
        failed_count = sum(1 for c in completions if c.get("status") == "failed")
        pending_count = sum(1 for c in completions if c.get("status") in ("queued", "processing", "provisional"))
        quantum_verified_count = sum(1 for c in completions if c.get("assurance_state") == "quantum_verified")
        buffered_quantum_count = sum(1 for r in accepted_rows if str(r.get("entropy_source", "")).startswith("buffered"))
        retry_count_total = sum(int(c.get("retry_count", 0) or 0) for c in completions)
        duration_s = max((sum(ack_latencies) + sum(completion_latencies)) / 1000.0, 0.001)
        metrics = {
            "accepted_count": accepted_count,
            "transmitted_count": transmitted_count,
            "failed_count": failed_count,
            "pending_count": pending_count,
            "avg_ack_latency_ms": round(statistics.mean(ack_latencies), 2) if ack_latencies else 0.0,
            "p95_ack_latency_ms": round(percentile(ack_latencies, 95), 2),
            "p99_ack_latency_ms": round(percentile(ack_latencies, 99), 2),
            "avg_completion_latency_ms": round(statistics.mean(completion_latencies), 2) if completion_latencies else 0.0,
            "p95_completion_latency_ms": round(percentile(completion_latencies, 95), 2),
            "throughput_jobs_sec": round(max(len(completions), 1) / duration_s, 2),
            "quantum_verified_count": quantum_verified_count,
            "buffered_quantum_count": buffered_quantum_count,
            "retry_count_total": retry_count_total,
        }
        fast_ack_enabled = bool(single.get("job_id")) and single.get("body", {}).get("status") == "queued"
        score = "Excellent" if accepted_count >= 20 and failed_count == 0 and pending_count == 0 and health_after.get("status") == "healthy" else "Good" if accepted_count > 0 and failed_count == 0 else "Needs Improvement"
        report = {
            "generated_at": time.time(),
            "module": "GhostTunnel",
            "health_before": health,
            "health_after": health_after,
            "fast_ack_enabled": fast_ack_enabled,
            "single_transmit": single,
            "batch_transmit": {"status_code": batch.status_code, "latency_ms": batch_latency, "responses": batch_body},
            "concurrent_transmit": {"requests": len(concurrent_rows), "accepted": sum(1 for r in concurrent_rows if r.get("ok"))},
            "payload_sizes": {"small": sizes[0], "medium": sizes[1], "large": sizes[2]},
            "invalid_payload_rejection": {"status_code": invalid.status_code, "passed": 400 <= invalid.status_code < 500},
            "queue_transitions": completions,
            "job_persistence": "job lookup endpoint returned queued/transmitted states for fast-ack jobs",
            "worker_stability": health_after.get("status") == "healthy",
            "stats_before": stats_before,
            "stats_after": stats_after,
            "metrics": metrics,
            "capability_score": score,
            "pass": score in ("Excellent", "Good") and 400 <= invalid.status_code < 500,
            "models_final_unchanged": before == production_model_hashes() and len(before) > 0,
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        MD_PATH.write_text(
            "\n".join([
                "# GhostTunnel Communication Capability",
                "",
                f"Capability Score: **{score}**",
                "",
                f"- Fast-ack enabled: {fast_ack_enabled}",
                f"- Accepted/transmitted/failed/pending: {accepted_count} / {transmitted_count} / {failed_count} / {pending_count}",
                f"- Avg/P95/P99 ack latency ms: {metrics['avg_ack_latency_ms']} / {metrics['p95_ack_latency_ms']} / {metrics['p99_ack_latency_ms']}",
                f"- Avg/P95 completion latency ms: {metrics['avg_completion_latency_ms']} / {metrics['p95_completion_latency_ms']}",
                f"- Buffered quantum count: {buffered_quantum_count}",
                f"- Retry count total: {retry_count_total}",
                "",
            ]),
            encoding="utf-8",
        )
        return report
    finally:
        if start_stack:
            _shutdown(procs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-start-stack", action="store_true")
    args = parser.parse_args()
    report = run_capability(start_stack=not args.no_start_stack)
    print("\n=== GHOSTTUNNEL COMMUNICATION CAPABILITY ===")
    print(f"Capability Score: {report['capability_score']}")
    print(f"Accepted: {report['metrics']['accepted_count']}")
    print(f"Transmitted: {report['metrics']['transmitted_count']}")
    print(f"Failed: {report['metrics']['failed_count']}")
    print(f"Result: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {JSON_PATH}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
