"""Phase 12.11 MutantShield detection capability validation."""
from __future__ import annotations

import argparse
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
from phase8_common import oracle_payload, percentile, production_model_hashes  # noqa: E402

OUT_DIR = ROOT / "reports" / "final" / "module_capabilities"
JSON_PATH = OUT_DIR / "mutantshield_detection_capability.json"
MD_PATH = OUT_DIR / "mutantshield_detection_capability.md"


def _read(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        return {}


def _hashes() -> Dict[str, str]:
    return production_model_hashes()


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


def _artifact_status() -> Dict[str, Any]:
    try:
        from mutantshield.evolution.config import get_config
        from mutantshield.evolution.model_coverage import discover_production_artifacts

        artifacts = discover_production_artifacts(get_config())
    except Exception as exc:
        return {"loaded": False, "error": str(exc), "artifacts": {}}
    required = ["XGBoost", "AutoEncoder", "LSTM", "GNN", "FusionMLP"]
    found = {name: bool(artifacts.get(name)) for name in required}
    return {
        "loaded": all(found.values()),
        "required_found": found,
        "artifacts": artifacts,
        "feature_schema_validation": "validated_by_phase9_phase10_feature_mapping_reports",
        "model_consensus": "FusionEngine ensemble artifacts present; exact per-sample consensus is reported through Oracle Core action/detection responses.",
    }


def _dataset_metrics() -> Dict[str, Any]:
    bench = _read(ROOT / "reports" / "final" / "oracle_final_benchmark_report.json")
    sections = bench.get("sections", {})
    cse = sections.get("cse_cic_ids2018_generalization", {})
    doh = sections.get("dohbrw_anomaly_detection", {})
    model_coverage = (sections.get("evolution_engine_safety") or {}).get("model_coverage", {})
    return {
        "cic_ids2017_baseline": _read(ROOT / "reports" / "evolution" / "production_baseline_metrics.json"),
        "unsw_nb15_validation": _read(ROOT / "reports" / "evolution" / "fair_production_baseline_metrics.json"),
        "cse_cic_ids2018": {
            "production_recall": cse.get("production_recall"),
            "initial_candidate_recall": cse.get("initial_candidate_recall"),
            "hoic_repair_candidate_recall": cse.get("hoic_repair_candidate_recall"),
            "hoic_recall_before": cse.get("hoic_recall_before"),
            "hoic_recall_after": cse.get("hoic_recall_after"),
            "false_allows_before": cse.get("false_allows_before"),
            "false_allows_after": cse.get("false_allows_after"),
            "p95_latency_ms": cse.get("p95_latency_ms"),
            "status": cse.get("status"),
        },
        "dohbrw": {
            "production_mapped_path_recall": doh.get("production_mapped_path_recall"),
            "native_adapter_recall": doh.get("native_adapter_recall"),
            "native_adapter_f1": doh.get("native_adapter_f1"),
            "benign_fpr": doh.get("benign_fpr"),
            "adversarial_recall": doh.get("adversarial_recall"),
            "pipeline_p95_latency_ms": doh.get("pipeline_p95_latency_ms"),
            "candidate_routing_readiness": doh.get("candidate_routing_readiness"),
        },
        "production_vs_candidate_comparison": {
            "cse_before_after_improvement": {
                "recall": [cse.get("production_recall"), cse.get("hoic_repair_candidate_recall")],
                "false_allows": [cse.get("false_allows_before"), cse.get("false_allows_after")],
            },
            "dohbrw_mapped_vs_native_improvement": {
                "recall": [doh.get("production_mapped_path_recall"), doh.get("native_adapter_recall")],
                "fpr": doh.get("benign_fpr"),
            },
        },
        "model_coverage": model_coverage,
        "honesty_notes": [
            "Production supports CIC/CICFlowMeter-style feature domains.",
            "CSE repair candidate handles validated CSE attack families, including HOIC.",
            "DoHBrw native adapter handles the DoHBrw anomaly domain.",
            "Unknown domains require adapters or reviewed evidence.",
            "LSTM/GNN production inference is active; candidate retraining is contract-gated.",
        ],
    }


def _system_path() -> Dict[str, Any]:
    samples = [
        oracle_payload(flow_id=f"ms-benign-{uuid.uuid4().hex[:8]}", risk_score=0.12, risk_label="LOW", is_attack=False, attack_family="benign"),
        oracle_payload(flow_id=f"ms-cse-{uuid.uuid4().hex[:8]}", risk_score=0.93, risk_label="HIGH", is_attack=True, attack_family="DDOS attack-HOIC", confidence_band="HIGH"),
        oracle_payload(flow_id=f"ms-doh-{uuid.uuid4().hex[:8]}", risk_score=0.88, risk_label="HIGH", is_attack=True, attack_family="DoHBrw-anomaly", confidence_band="HIGH"),
        oracle_payload(flow_id=f"ms-med-{uuid.uuid4().hex[:8]}", risk_score=0.52, risk_label="MEDIUM", is_attack=False, attack_family="uncertain"),
    ]
    records: List[Dict[str, Any]] = []
    latencies: List[float] = []
    for payload in samples:
        t0 = time.perf_counter()
        try:
            r = requests.post("http://127.0.0.1:8000/oracle/process", json=payload, timeout=20)
            elapsed = round((time.perf_counter() - t0) * 1000, 2)
            latencies.append(elapsed)
            body = r.json() if r.content else {}
            records.append({
                "flow_id": payload.get("flow_id"),
                "attack_family": payload.get("attack_family"),
                "status_code": r.status_code,
                "latency_ms": elapsed,
                "degraded": r.status_code == 207 or bool(body.get("failed_services")),
                "failed": r.status_code >= 500,
                "final_action": (body.get("action") or {}).get("final_action"),
                "ethicq_decision": (body.get("ethics") or {}).get("action") or (body.get("ethics") or {}).get("decision"),
                "audit_logged": bool((body.get("audit") or {}).get("logged", True)),
                "assurance_states": body.get("assurance_states"),
            })
        except Exception as exc:
            records.append({"flow_id": payload.get("flow_id"), "error": str(exc), "failed": True})
    return {
        "samples": len(samples),
        "success": sum(1 for r in records if r.get("status_code") in (200, 207)),
        "degraded": sum(1 for r in records if r.get("degraded")),
        "failed": sum(1 for r in records if r.get("failed")),
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0.0,
        "p95_latency_ms": round(percentile(latencies, 95), 2),
        "throughput_samples_sec": round(len(samples) / max(sum(latencies) / 1000.0, 0.001), 2),
        "final_action_distribution": {a: sum(1 for r in records if r.get("final_action") == a) for a in sorted({str(r.get("final_action")) for r in records})},
        "records": records,
    }


def _score(dataset: Dict[str, Any], system: Dict[str, Any]) -> str:
    cse_recall = float(((dataset.get("cse_cic_ids2018") or {}).get("hoic_repair_candidate_recall")) or 0)
    doh_recall = float(((dataset.get("dohbrw") or {}).get("native_adapter_recall")) or 0)
    doh_f1 = float(((dataset.get("dohbrw") or {}).get("native_adapter_f1")) or 0)
    stable = system.get("failed") == 0 and system.get("degraded") == 0
    if cse_recall >= 0.95 and doh_recall >= 0.95 and doh_f1 >= 0.95 and stable:
        return "Excellent"
    if cse_recall >= 0.8 and doh_recall >= 0.9 and stable:
        return "Good"
    return "Needs Improvement"


def run_capability(start_stack: bool = True) -> Dict[str, Any]:
    before = _hashes()
    procs: List[Any] = []
    if start_stack:
        kill_all_ports()
        procs = start_services()
        wait_for_health(max_wait_s=120.0)
    try:
        artifacts = _artifact_status()
        dataset = _dataset_metrics()
        system = _system_path()
        capability_score = _score(dataset, system)
        report = {
            "generated_at": time.time(),
            "module": "MutantShield",
            "purpose": "IDS/detection capability validation across production ensemble, candidates, and Oracle path.",
            "standalone": artifacts,
            "dataset_capability": dataset,
            "system_level_detection_path": system,
            "metrics": {
                "accuracy": None,
                "precision": None,
                "recall": {
                    "cse_repair_candidate": (dataset.get("cse_cic_ids2018") or {}).get("hoic_repair_candidate_recall"),
                    "dohbrw_native_adapter": (dataset.get("dohbrw") or {}).get("native_adapter_recall"),
                },
                "f1": {"dohbrw_native_adapter": (dataset.get("dohbrw") or {}).get("native_adapter_f1")},
                "false_positive_rate": {"dohbrw_native_adapter": (dataset.get("dohbrw") or {}).get("benign_fpr")},
                "false_negative_rate": {
                    "cse_repair_candidate": None if (dataset.get("cse_cic_ids2018") or {}).get("hoic_repair_candidate_recall") is None else round(1 - float((dataset.get("cse_cic_ids2018") or {}).get("hoic_repair_candidate_recall")), 6),
                    "dohbrw_native_adapter": None if (dataset.get("dohbrw") or {}).get("native_adapter_recall") is None else round(1 - float((dataset.get("dohbrw") or {}).get("native_adapter_recall")), 6),
                },
                "confusion_matrix": "See source phase reports; not recomputed here to avoid faking absent raw labels.",
                "per_attack_family_recall": "Validated by CSE repair reports; consolidated recall included above.",
                "inference_avg_latency_ms": system.get("avg_latency_ms"),
                "inference_p95_latency_ms": system.get("p95_latency_ms"),
                "throughput_samples_sec": system.get("throughput_samples_sec"),
            },
            "capability_score": capability_score,
            "pass": capability_score in ("Excellent", "Good") and artifacts.get("loaded") and system.get("failed") == 0,
            "models_final_unchanged": before == _hashes() and len(before) > 0,
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        MD_PATH.write_text(
            "\n".join([
                "# MutantShield Detection Capability",
                "",
                f"Capability Score: **{capability_score}**",
                "",
                f"- Production artifacts loaded: {artifacts.get('loaded')}",
                f"- CSE repair recall: {(dataset.get('cse_cic_ids2018') or {}).get('hoic_repair_candidate_recall')}",
                f"- DoHBrw native recall/F1: {(dataset.get('dohbrw') or {}).get('native_adapter_recall')} / {(dataset.get('dohbrw') or {}).get('native_adapter_f1')}",
                f"- System path success/degraded/failed: {system.get('success')} / {system.get('degraded')} / {system.get('failed')}",
                "",
                "## Honest Limits",
                "",
                "- Production supports CIC/CICFlowMeter-style domains.",
                "- CSE and DoHBrw capability depends on validated candidates/adapters.",
                "- Unknown domains require adapters or reviewed evidence.",
                "- LSTM/GNN inference is active; retraining is contract-gated.",
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
    print("\n=== MUTANTSHIELD DETECTION CAPABILITY ===")
    print(f"Capability Score: {report['capability_score']}")
    print(f"Production Artifacts Loaded: {report['standalone'].get('loaded')}")
    print(f"System Path Failed: {report['system_level_detection_path'].get('failed')}")
    print(f"Result: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"Report: {JSON_PATH}")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
